"""Unit tests for the `XMLKMLParser` class in the `kmlorm.parsers.xml_parser` module.

This test suite covers a wide range of KML and KMZ parsing scenarios, including:
- Parsing coordinate strings in various formats and handling edge cases.
- Detecting and extracting KML content from KMZ (ZIP) files, both from bytes and files.
- Handling invalid XML and KMZ content, ensuring appropriate exceptions are raised.
- Parsing KML from strings, files, and URLs, including both KML and KMZ sources.
- Extracting document-level information such as name and description.
- Parsing and constructing KML model objects: Placemark, Point, Path (LineString), Polygon,
    MultiGeometry, and Folder.
- Handling nested and mixed KML structures, including nested Folders and MultiGeometries.
- Parsing ExtendedData, SchemaData, and Data elements within Placemarks.
- Testing helper methods for extracting text and boolean values from XML elements.
- Ensuring robust error handling and exception wrapping for model constructors and parsing logic.
- Verifying correct handling of KML edge cases, such as polygons with multiple inner boundaries
    and malformed coordinate strings.
- Ensuring that the parser correctly associates parent names with child geometries.
- Testing the parser's ability to handle KMZ files with multiple KML files, picking the first one.
- Verifying that the parser's internal helper methods behave correctly under error conditions
    via monkeypatching.

Dependencies:
- `pytest` for test execution and exception assertions.
- `lxml` for XML parsing in tests that require parent element access.
- `zipfile` and `io` for in-memory KMZ creation and manipulation.
- `kmlorm` models and exceptions for constructing and validating parsed objects.

Each test is designed to be self-contained and to assert the expected behavior of the
`XMLKMLParser` under both normal and erroneous conditions.
"""

# pylint: disable=import-outside-toplevel, protected-access, too-many-lines, too-many-public-methods
import io
import zipfile

from pathlib import Path
from typing import Any, Optional
import pytest
from kmlorm.parsers.xml_parser import XMLKMLParser
from kmlorm.core.exceptions import KMLParseError


class TestXMLKMLParser:
    """
    Test suite for the XMLKMLParser class, covering a wide range of KML and KMZ parsing scenarios.

    This class contains tests for:
    - Parsing coordinate strings in various formats and handling edge cases.
    - Detecting and extracting KML content from KMZ (zip) files, both from bytes and files.
    - Handling invalid XML and KMZ content, ensuring appropriate exceptions are raised.
    - Parsing KML documents from strings, files, and URLs, including both KML and KMZ sources.
    - Extracting document-level information such as name and description.
    - Parsing and constructing KML model objects: Placemark, Point, Path (LineString),
        Polygon, MultiGeometry, and Folder.
    - Handling nested and mixed KML structures, including nested Folders and MultiGeometries.
    - Parsing ExtendedData, SchemaData, and Data elements within Placemarks.
    - Helper methods for extracting text and boolean values from XML elements.
    - Ensuring robust error handling in model constructors and parser methods via monkeypatching.
    - Handling edge cases such as missing files, malformed KMZs, and coordinate parsing anomalies.

    Dependencies:
    - pytest for assertions and exception testing.
    - lxml for XML parsing in tests that require parent element access.
    - io, zipfile, and monkeypatching for simulating file and network operations.

    Each test is designed to validate a specific aspect of the XMLKMLParser's functionality
        and error handling.
    """

    def test_parse_coordinate_string_various(self) -> None:
        """
        Test the _parse_coordinate_string method of XMLKMLParser with various input formats.

        This test verifies that:
        - A canonical KML coordinate string (with multiple coordinates in "lon,lat,alt" format)
            is parsed correctly into a list of tuples of floats.
        - An empty string input returns an empty list.
        """
        parser = XMLKMLParser()
        # Use canonical KML coordinate format where each coordinate is lon,lat,alt
        s = "10,20,0 11,21,0 12,22,5"
        # pylint: disable=protected-access
        coords = parser._parse_coordinate_string(s)
        assert coords == [(10.0, 20.0, 0.0), (11.0, 21.0, 0.0), (12.0, 22.0, 5.0)]

        # empty string
        assert not parser._parse_coordinate_string("")

    def test_is_zip_content_and_extract_kmz_from_bytes(self) -> None:
        """
        Test that verifies whether the XMLKMLParser correctly identifies KMZ (zip) content
            from bytes
        and successfully extracts the KML content from an in-memory KMZ archive.

        Steps:
        1. Creates an in-memory KMZ file containing a simple KML document.
        2. Asserts that the KMZ data is recognized as zip content by _is_zip_content.
        3. Extracts the KML content from the KMZ bytes using _extract_kmz_from_bytes.
        4. Asserts that the extracted content contains the expected KML structure.
        """
        # Create an in-memory KMZ (zip) containing doc.kml
        kml_text = "<kml><Document><name>X</name></Document></kml>"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("doc.kml", kml_text)
        data = buf.getvalue()

        # pylint: disable=protected-access
        assert XMLKMLParser._is_zip_content(data) is True

        extracted = XMLKMLParser._extract_kmz_from_bytes(data)
        assert "<Document>" in extracted

    def test_parse_from_string_invalid_xml_raises(self) -> None:
        """
        Test that parsing an invalid XML string with missing closing tags raises a KMLParseError.
        """
        parser = XMLKMLParser()
        invalid = "<kml><Document><name>Bad</name>"  # missing closing tags
        with pytest.raises(KMLParseError):
            parser.parse_from_string(invalid)

    def test_parse_from_string_extraction_exception_wrapped(self, monkeypatch: Any) -> None:
        """
        Test that XMLKMLParser.parse_from_string raises a KMLParseError when an unexpected exception
        occurs during element extraction, and that the error message contains 'Error parsing KML'.

        This test uses monkeypatch to simulate a failure in the _extract_all_elements method,
        ensuring that such internal errors are properly wrapped and reported as KMLParseError.
        """
        parser = XMLKMLParser()

        # Make parser._extract_all_elements raise to simulate unexpected extraction failure
        def raise_exc(root: Any) -> None:
            raise RuntimeError("boom")

        monkeypatch.setattr(parser, "_extract_all_elements", raise_exc)

        minimal = '<kml xmlns="http://www.opengis.net/kml/2.2"><Document/></kml>'
        with pytest.raises(KMLParseError) as excinfo:
            parser.parse_from_string(minimal)

        assert "Error parsing KML" in str(excinfo.value)

    def test_parse_from_string_parses_basic_placemark(self) -> None:
        """
        Test that XMLKMLParser.parse_from_string correctly parses a basic KML Placemark
        from a string.

        This test verifies:
        - The parser can handle a KML string containing a Document with a name and a
            single Placemark.
        - The returned document name matches the expected value.
        - At least one parsed element represents the Placemark with the expected name ("PM One").
        - The test is skipped if the 'lxml' library is not available, as it is required for parsing.

        KML sample includes:
        - Document name
        - Placemark with id, name, Point coordinates, and ExtendedData
        """
        # This test requires lxml because xml.etree.ElementTree elements lack getparent()
        pytest.importorskip("lxml")

        parser = XMLKMLParser()
        kml = """
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document>
            <name>DocName</name>
            <description>Test XML Document</description>
            <Placemark id="pm1">
              <name>PM One</name>
              <Point><coordinates>10,20,5</coordinates></Point>
              <ExtendedData>
                <Data name="foo"><value>bar</value></Data>
              </ExtendedData>
            </Placemark>
          </Document>
        </kml>
        """

        doc_name, doc_desc, elements = parser.parse_from_string(kml)
        assert doc_desc is not None
        assert doc_name == "DocName"
        # Expect at least one element representing the Placemark
        assert any(getattr(e, "name", None) == "PM One" for e in elements)

    def test_kmz_file_extraction_and_bad_kmz(self, tmp_path: Path) -> None:
        """
        Tests the extraction of KML content from a valid KMZ file and verifies that attempting
        to extract from an invalid KMZ file raises a KMLParseError.

        This test performs the following:
        - Creates a valid KMZ file containing a simple KML document and checks that the extracted
            content includes the expected document name.
        - Creates an invalid KMZ file (a plain text file with a .kmz extension) and asserts that
            extracting from it raises a KMLParseError.
        """
        # Good KMZ file on disk
        kml_text = "<kml><Document><name>KMZDoc</name></Document></kml>"
        kmz_path = tmp_path / "test.kmz"
        with zipfile.ZipFile(str(kmz_path), "w") as z:
            z.writestr("doc.kml", kml_text)

        # pylint: disable=protected-access
        extracted = XMLKMLParser._extract_kmz(str(kmz_path))
        assert "KMZDoc" in extracted

        # Bad KMZ (not a zip) should raise KMLParseError
        bad_path = tmp_path / "bad.kmz"
        bad_path.write_text("not a zip file")
        with pytest.raises(KMLParseError):
            XMLKMLParser._extract_kmz(str(bad_path))

    def test_placemark_linestring_and_polygon_and_multigeometry(self) -> None:
        """
        Test parsing of KML Placemarks containing LineString, Polygon, MultiGeometry, and
        empty geometry elements.

        This test verifies that:
        - Placemarks with different geometry types (LineString, Polygon, MultiGeometry, and
            no geometry) are correctly parsed.
        - The names of all Placemarks are extracted and present in the parsed elements.
        - At least one Path object is created from a LineString, and its coordinates are parsed.
        - At least one Polygon object is created with a parsed outer boundary.
        - MultiGeometry elements are correctly associated with their parent Placemark.
        """
        pytest.importorskip("lxml")

        parser = XMLKMLParser()

        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            "<name>TestDoc</name>"
            "<description>Text KML Document</description>"
            '<Placemark id="pl1"><name>Line PM</name>'
            "<LineString><coordinates>10,20 11,21</coordinates></LineString>"
            "</Placemark>"
            '<Placemark id="pl2"><name>Poly PM</name>'
            "<Polygon>"
            "<outerBoundaryIs><LinearRing>"
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs>"
            "</Polygon></Placemark>"
            '<Placemark id="pl3"><name>MG PM</name>'
            "<MultiGeometry>"
            "<Point><coordinates>5,5,0</coordinates></Point>"
            "<LineString><coordinates>6,6 7,7</coordinates></LineString>"
            "</MultiGeometry></Placemark>"
            '<Placemark id="pl4"><name>NoGeom</name></Placemark>'
            "</Document></kml>"
        )

        doc_name, doc_desc, elements = parser.parse_from_string(kml)
        assert doc_name is not None
        assert doc_desc is not None
        # Check Placemark names exist
        names = {getattr(e, "name", None) for e in elements}
        assert "Line PM" in names
        assert "Poly PM" in names
        assert "MG PM" in names or any(getattr(e, "multigeometry", None) for e in elements)
        assert "NoGeom" in names

        # Ensure at least one Path was created and it has parsed coordinates
        paths = [e for e in elements if e.__class__.__name__ == "Path"]
        assert paths, "Expected at least one Path from LineString"
        assert any(getattr(p, "coordinates", []) for p in paths)

        # Ensure a Polygon exists with an outer boundary parsed
        polys = [e for e in elements if e.__class__.__name__ == "Polygon"]
        assert any(getattr(p, "outer_boundary", None) for p in polys)

        # MultiGeometry should be associated with its Placemark
        mg_placemarks = [e for e in elements if getattr(e, "multigeometry", None) is not None]
        assert any(mg_placemarks)

    def test_folder_and_standalone_geometries(self) -> None:
        """
        Tests the XMLKMLParser's ability to correctly parse a KML document containing
        nested Folders, Placemarks, standalone geometries (Point, MultiGeometry), and verifies
        that top-level elements are correctly identified.

        The test KML includes:
          - A Folder with nested Folders and Placemarks containing Points and a LineString.
          - Standalone Point and MultiGeometry elements at the Document level.

        Asserts that the parser returns a list of elements at the top level that includes:
          - At least one Folder
          - At least one Point
          - At least one MultiGeometry
        """
        pytest.importorskip("lxml")

        parser = XMLKMLParser()

        kml = """
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document>
            <name>FolderAndStandaloneGeometries</name>
            <description>Testing Folder and Standalone Geometries</description>
            <Folder id="f1"><name>F1</name>
              <Placemark id="p1"><name>P1</name>
                <Point><coordinates>1,2</coordinates></Point>
              </Placemark>
              <Folder id="f2"><name>F2</name>
                <Placemark id="p2"><name>P2</name>
                  <Point><coordinates>2,3</coordinates></Point>
                </Placemark>
              </Folder>
              <LineString id="ls1"><coordinates>3,4 4,5</coordinates></LineString>
            </Folder>
            <Point id="pt_standalone"><coordinates>9,9</coordinates></Point>
            <MultiGeometry id="mg_top"><Point><coordinates>7,7</coordinates></Point></MultiGeometry>
          </Document>
        </kml>
        """

        doc_name, doc_desc, elements = parser.parse_from_string(kml)
        assert doc_name is not None
        assert doc_desc is not None
        # Top-level should include the Folder, standalone Point and MultiGeometry
        assert any(e.__class__.__name__ == "Folder" for e in elements)
        assert any(e.__class__.__name__ == "Point" for e in elements)
        assert any(e.__class__.__name__ == "MultiGeometry" for e in elements)

    def test_helpers_get_text_and_get_bool(self) -> None:
        """
        Test the helper methods `_get_text` and `_get_bool` of the `XMLKMLParser` class.

        This test verifies:
        - `_get_text` correctly strips whitespace and retrieves text from a child element,
            or returns a default value if the element is missing.
        - `_get_bool` correctly parses boolean values from child elements, interpreting
            "true" as `True`, "0" as `False`, and returning a default value if the element
             is missing.

        Requires the `lxml` library.
        """
        pytest.importorskip("lxml")
        # pylint: disable=import-outside-toplevel, protected-access
        from lxml import etree as _et

        parser = XMLKMLParser()

        parent = _et.fromstring("<root><a>  text  </a><b>true</b><c>0</c></root>")
        assert parser._get_text(parent, "a") == "text"
        assert parser._get_text(parent, "missing", default="x") == "x"
        assert parser._get_bool(parent, "b", default=False) is True
        assert parser._get_bool(parent, "c", default=True) is False

    def test_standalone_geometries_and_nested_multigeometry(self) -> None:
        """
        Test that the XMLKMLParser correctly parses standalone geometries and nested
        MultiGeometry elements from a KML string.

        This test verifies:
        - Standalone LineString elements are parsed as Path objects.
        - Standalone Polygon elements are parsed as Polygon objects.
        - Standalone Point elements with coordinates are parsed as Point objects.
        - Nested MultiGeometry elements are correctly parsed and appear in the resulting
            elements list.
        """
        pytest.importorskip("lxml")

        parser = XMLKMLParser()

        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            "<name>standalonegeometriesandnestedmultigeometry</name>"
            "<description>Test Standalone Geometries and Nested MultiGeometries</description>"
            '<LineString id="ls"><coordinates>1,1 2,2</coordinates></LineString>'
            '<Polygon id="poly">'
            "<outerBoundaryIs><LinearRing>"
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs>"
            "</Polygon>"
            '<Point id="pt"><coordinates>5,5,0</coordinates></Point>'
            '<MultiGeometry id="mg">'
            "<MultiGeometry>"
            "<Point><coordinates>9,9</coordinates></Point>"
            "</MultiGeometry>"
            "</MultiGeometry>"
            "</Document></kml>"
        )

        doc_name, doc_desc, elements = parser.parse_from_string(kml)
        assert doc_name is not None
        assert doc_desc is not None
        # Check for standalone Path (LineString)
        assert any(e.__class__.__name__ == "Path" for e in elements)

        # Check for standalone Polygon
        assert any(e.__class__.__name__ == "Polygon" for e in elements)

        # Check for standalone Point with coordinates
        pts = [e for e in elements if e.__class__.__name__ == "Point"]
        assert any(getattr(p, "coordinates", None) for p in pts)

        # Check nested MultiGeometry was parsed (should appear at least once)
        assert any(e.__class__.__name__ == "MultiGeometry" for e in elements)

    def test_extended_data_schemadata_and_data_parsing(self) -> None:
        """
        Test that the XMLKMLParser correctly parses <ExtendedData> elements
        containing both <Data> and <SchemaData> child elements.

        This test verifies that:
        - <Data> elements with a 'name' attribute and a <value> child are parsed
            and accessible via the 'extended_data' dictionary.
        - <SchemaData> elements with <SimpleData> children are also parsed and
            accessible via the 'extended_data' dictionary.
        - The correct values are extracted for both types of data elements.

        Requires the 'lxml' library to be installed.
        """
        pytest.importorskip("lxml")

        parser = XMLKMLParser()
        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            '<Placemark id="x">'
            "<ExtendedData>"
            '<Data name="d1"><value>v1</value></Data>'
            '<SchemaData><SimpleData name="s1">sv1</SimpleData></SchemaData>'
            "</ExtendedData>"
            "</Placemark>"
            "</Document></kml>"
        )

        _, _, elements = parser.parse_from_string(kml)
        pm = next((e for e in elements if getattr(e, "id", None) == "x"), None)
        assert pm is not None
        assert pm.extended_data.get("d1") == "v1"
        assert pm.extended_data.get("s1") == "sv1"

    def test_parse_from_url_invalid_url_format_raises(self) -> None:
        """
        Test that XMLKMLParser.parse_from_url raises a KMLParseError when given an
            invalid URL format.
        """
        parser = XMLKMLParser()
        with pytest.raises(KMLParseError):
            parser.parse_from_url("not-a-url")

    def test_extract_kmz_no_kml_and_bad_bytes(self) -> None:
        """
        Test the behavior of XMLKMLParser._extract_kmz_from_bytes when handling KMZ
        files with no KML content and invalid KMZ data.

        This test verifies two scenarios:
        1. When a KMZ (zip) archive does not contain any KML file, the method
            should raise a KMLParseError.
        2. When the input bytes are not a valid zip archive, the method should
            also raise a KMLParseError.
        """
        # no-kml inside zip should raise
        # pylint: disable=protected-access
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("readme.txt", "hello")
        data = buf.getvalue()

        with pytest.raises(KMLParseError):
            XMLKMLParser._extract_kmz_from_bytes(data)

        # bad bytes should raise Invalid KMZ content
        with pytest.raises(KMLParseError):
            XMLKMLParser._extract_kmz_from_bytes(b"not a zip")

    def test_is_zip_content_false(self) -> None:
        """
        Test that the _is_zip_content method returns False when provided with
        non-zip binary content.
        """
        # pylint: disable=protected-access
        assert XMLKMLParser._is_zip_content(b"hello") is False

    def test_create_point_polygon_linestring_with_parent(self) -> None:
        """
        Test that KML geometry elements (Point, Polygon, LineString) created from XML elements
        correctly inherit the parent Placemark's name attribute.

        This test verifies:
        - A Point inside a Placemark receives the Placemark's name as its own name.
        - A Polygon inside a Placemark receives the Placemark's name as its own name.
        - A LineString inside a Placemark receives the Placemark's name as its own name.

        Requires: lxml
        """
        pytest.importorskip("lxml")

        from lxml import etree as _et

        parser = XMLKMLParser()

        # Point inside Placemark should pick up parent name
        xml = (
            '<Placemark xmlns="http://www.opengis.net/kml/2.2">'
            "<name>ParentPoint</name>"
            "<Point><coordinates>1,2,3</coordinates></Point>"
            "</Placemark>"
        )
        root = _et.fromstring(xml)
        point_elem = root.find(".//{http://www.opengis.net/kml/2.2}Point")
        pt = parser._create_point_from_element(point_elem)
        assert pt is not None
        assert getattr(pt, "name", None) == "ParentPoint"

        # Polygon inside Placemark
        xmlp = (
            '<Placemark xmlns="http://www.opengis.net/kml/2.2">'
            "<name>ParentPoly</name>"
            "<Polygon><outerBoundaryIs><LinearRing>"
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon>"
            "</Placemark>"
        )
        rootp = _et.fromstring(xmlp)
        poly_elem = rootp.find(".//{http://www.opengis.net/kml/2.2}Polygon")
        poly = parser._create_polygon_from_element(poly_elem)
        assert poly is not None
        assert getattr(poly, "name", None) == "ParentPoly"

        # LineString inside Placemark
        xmls = (
            '<Placemark xmlns="http://www.opengis.net/kml/2.2">'
            "<name>ParentLine</name>"
            "<LineString><coordinates>10,10 11,11</coordinates></LineString>"
            "</Placemark>"
        )
        roots = _et.fromstring(xmls)
        ls_elem = roots.find(".//{http://www.opengis.net/kml/2.2}LineString")
        path = parser._create_path_from_linestring(ls_elem)
        assert path is not None
        assert getattr(path, "name", None) == "ParentLine"

    def test_parse_from_url_kml_and_kmz_bytes(self, monkeypatch: Any) -> None:
        """
        Test the XMLKMLParser's ability to parse KML and KMZ files from a URL.

        This test monkeypatches the `urlopen` function to return controlled KML and
        KMZ byte streams, simulating the retrieval of KML and KMZ files from a
        remote URL. It verifies that the parser correctly extracts the document
        name from both KML and KMZ formats.

        Steps:
            1. Monkeypatch `urlopen` to return a dummy response containing KML bytes.
            2. Parse the KML bytes from a fake URL and assert the document name is as expected.
            3. Create a KMZ (zipped KML) in memory, monkeypatch `urlopen` to return the KMZ bytes.
            4. Parse the KMZ bytes from a fake URL and assert the document name is as expected.

        Args:
            monkeypatch (Any): pytest's monkeypatch fixture for patching functions.
            tmp_path (Path): pytest's temporary directory fixture (not used in this test).

        Asserts:
            The parsed document name from both KML and KMZ sources matches the expected value.
        """

        # Monkeypatch urlopen to return controlled bytes
        class DummyResp:
            """
            A dummy response class that simulates a file-like object for testing purposes.

            Attributes:
                _data (bytes): The data to be returned by the read() method.

            Methods:
                __init__(data: bytes): Initializes the DummyResp with the given data.
                __enter__(): Enables use as a context manager, returns self.
                __exit__(exc_type, exc, tb): Handles context manager exit, returns to
                    propagate exceptions.
                read(): Returns the stored data as bytes.
            """

            def __init__(self, data: bytes):
                self._data = data

            def __enter__(self) -> "DummyResp":
                """
                Enter the runtime context related to this object.

                Returns:
                    self: The context manager instance itself.
                """
                return self

            def __exit__(
                self, exc_type: Optional[type[BaseException]], exc: Optional[BaseException], tb: Any
            ) -> None:
                """
                Exit the runtime context and handle any exception raised within the context.

                Args:
                    exc_type (Any): The type of the exception raised (if any).
                    exc (Any): The exception instance raised (if any).
                    tb (Any): The traceback object associated with the exception (if any).

                Returns:
                    bool: False to indicate that any exception should not be suppressed and
                        will be propagated.
                """
                return

            def read(self) -> Any:
                """
                Returns the stored data.

                Returns:
                    Any: The data stored in the instance.
                """
                return self._data

        parser = XMLKMLParser()

        # KML bytes
        kml_str = """<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>U</name>
        <description>d</description>
    </Document>
</kml>"""
        kml = kml_str.encode("utf-8")
        monkeypatch.setattr("kmlorm.parsers.xml_parser.urlopen", lambda url: DummyResp(kml))
        name, desc, elems = parser.parse_from_url("http://example.com/test.kml")
        assert desc is not None
        assert elems is not None
        assert name == "U"

        # KMZ bytes
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("doc.kml", kml)
        kmz_bytes = buf.getvalue()

        monkeypatch.setattr("kmlorm.parsers.xml_parser.urlopen", lambda url: DummyResp(kmz_bytes))
        name2, _, elems2 = parser.parse_from_url("http://example.com/test.kmz")
        assert elems2 is not None
        assert name2 == "U"

    def test_create_methods_handle_constructor_exceptions(self, monkeypatch: Any) -> None:
        """
        Test that XMLKMLParser's create methods gracefully handle exceptions raised
        by model constructors.

        This test uses monkeypatching to replace constructors of KML model classes (e.g.,
        Point, Placemark, Folder, MultiGeometry, Path) with a dummy class that always
        raises a RuntimeError. It verifies that the parser's internal creation methods
        (_create_placemark, _create_placemark_with_multigeometry, _create_folder,
        _create_multigeometry_from_element, _create_path_from_linestring)
        catch these exceptions and return None instead of propagating the error.

        Args:
            monkeypatch (Any): pytest's monkeypatch fixture for replacing attributes
                during the test.

        Raises:
            AssertionError: If any of the parser's create methods do not return None when the
                constructor raises an exception.
        """
        # Force module-level model constructors to raise so parser handles them
        import kmlorm.parsers.xml_parser as xml_parser_mod

        parser = XMLKMLParser()

        # Dummy elements for testing
        pytest.importorskip("lxml")
        from lxml import etree as _et

        # Placemark with Point
        placemark_xml = (
            '<Placemark xmlns="http://www.opengis.net/kml/2.2" id="x">'
            "<name>X</name><Point><coordinates>1,2,3</coordinates></Point></Placemark>"
        )
        placemark_elem = _et.fromstring(placemark_xml)
        point_elem = placemark_elem.find(".//{http://www.opengis.net/kml/2.2}Point")

        class BadCtor:  # pylint: disable=too-few-public-methods
            """
            A class that raises a RuntimeError upon instantiation.

            Intended for testing error handling in code that constructs objects.
            Any attempt to create an instance of BadCtor will result in a RuntimeError with
            the message "boom".

            Args:
                *args: Variable length argument list.
                **kwargs: Arbitrary keyword arguments.

            Raises:
                RuntimeError: Always raised when an instance is created.
            """

            def __init__(self, *args: Any, **kwargs: Any):
                raise RuntimeError("boom")

        # Monkeypatch Point to raise -> _create_placemark should catch and return None
        monkeypatch.setattr(xml_parser_mod, "Point", BadCtor)
        assert parser._create_placemark(placemark_elem, point_elem) is None

        # Monkeypatch Placemark to raise -> _create_placemark_with_multigeometry should return None

        monkeypatch.setattr(xml_parser_mod, "Placemark", BadCtor)
        # Build a MultiGeometry object to pass
        from kmlorm.models.multigeometry import MultiGeometry as RealMG

        real_mg = RealMG()
        assert parser._create_placemark_with_multigeometry(placemark_elem, real_mg) is None

        # Monkeypatch Folder/Path/MultiGeometry to raise in their constructors for
        # folder/parse tests
        monkeypatch.setattr(xml_parser_mod, "Folder", BadCtor)
        folder_xml = _et.fromstring(
            '<Folder xmlns="http://www.opengis.net/kml/2.2" id="f"><name>F</name></Folder>'
        )
        assert parser._create_folder(folder_xml) is None

        monkeypatch.setattr(xml_parser_mod, "MultiGeometry", BadCtor)
        mg_elem = _et.fromstring(
            '<MultiGeometry xmlns="http://www.opengis.net/kml/2.2"></MultiGeometry>'
        )
        assert parser._create_multigeometry_from_element(mg_elem) is None

        # Monkeypatch Path to raise for _create_path_from_linestring
        monkeypatch.setattr(xml_parser_mod, "Path", BadCtor)
        ls_elem = _et.fromstring(
            '<LineString xmlns="http://www.opengis.net/kml/2.2">'
            "<coordinates>1,2 2,3</coordinates></LineString>"
        )
        assert parser._create_path_from_linestring(ls_elem) is None

    def test_polygon_inner_boundaries_and_coordinate_edge_cases(self) -> None:
        """
        Test parsing of KML polygons with multiple inner boundaries and coordinate
        string edge cases.

        This test verifies that:
        - The XMLKMLParser correctly parses a Polygon element with multiple
            <innerBoundaryIs> elements, ensuring that all inner boundaries
            are detected and stored.
        - The parser's coordinate string parsing method (_parse_coordinate_string)
            handles edge cases, such as skipping invalid tokens (e.g., non-numeric
            strings) and correctly parsing both 2-value and 3-value coordinate tuples.

        Assertions:
        - At least one Polygon is parsed from the KML string.
        - The parsed Polygon contains at least two inner boundaries.
        - The coordinate string parser skips invalid tokens and parses available
            coordinates with 2 or 3 values.
        """
        pytest.importorskip("lxml")
        parser = XMLKMLParser()

        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            '<Placemark id="poly2">'
            "<Polygon>"
            "<outerBoundaryIs><LinearRing>"
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs>"
            "<innerBoundaryIs><LinearRing>"
            "<coordinates>0.2,0.2 0.8,0.2 0.8,0.8 0.2,0.8 0.2,0.2</coordinates>"
            "</LinearRing></innerBoundaryIs>"
            "<innerBoundaryIs><LinearRing>"
            "<coordinates>0.3,0.3 0.7,0.3 0.7,0.7 0.3,0.7 0.3,0.3</coordinates>"
            "</LinearRing></innerBoundaryIs>"
            "</Polygon>"
            "</Placemark>"
            "</Document></kml>"
        )

        _, _, elements = parser.parse_from_string(kml)
        polys = [e for e in elements if e.__class__.__name__ == "Polygon"]
        assert polys
        p = polys[0]
        # Expect two inner boundaries parsed
        assert getattr(p, "inner_boundaries", None) and len(p.inner_boundaries) >= 2

        # Coordinate parsing edge cases
        s = "10,20 abc 11,21 12,22,5 13,23"
        coords = parser._parse_coordinate_string(s)
        # Should skip 'abc' token and parse available 2- and 3-value coords
        assert any(len(c) in (2, 3) for c in coords)

    def test_folder_nested_mixed_contents(self) -> None:
        """
        Test that the XMLKMLParser correctly parses a KML structure with a root folder containing
        mixed content: placemarks, nested folders, and paths. Verifies that the root folder contains
        at least one placemark, one nested folder, and one path after parsing.
        """
        pytest.importorskip("lxml")
        parser = XMLKMLParser()

        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            '<Folder id="root">'
            "<name>Root</name>"
            '<Placemark id="p1"><Point><coordinates>1,1</coordinates></Point></Placemark>'
            '<Folder id="nested"><name>Nested</name>'
            '<Placemark id="p2"><Point><coordinates>2,2</coordinates></Point></Placemark>'
            "</Folder>"
            '<LineString id="lsroot"><coordinates>3,3 4,4</coordinates></LineString>'
            "</Folder>"
            "</Document></kml>"
        )

        _, _, elements = parser.parse_from_string(kml)
        folder = next((e for e in elements if e.__class__.__name__ == "Folder"), None)
        assert folder is not None
        # Folder should contain a placemark, nested folder, and a path
        assert folder.placemarks.count() >= 1
        assert folder.folders.count() >= 1
        assert folder.paths.count() >= 1

    def test_parse_from_file_kmz_and_missing_file(self, tmp_path: Path) -> None:
        """
        Tests the XMLKMLParser's ability to parse KML data from a KMZ file and handle missing files.

        - Creates a KMZ file containing a simple KML document and verifies that the parser
            correctly extracts the document name.
        - Asserts that attempting to parse a non-existent file raises a FileNotFoundError.

        Args:
            tmp_path (Path): Temporary directory provided by pytest for file operations.
        """
        parser = XMLKMLParser()

        # create a KMZ file on disk
        kml_text = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document><name>FromFile</name><description>d</description></Document></kml>"
        )
        kmz_path = tmp_path / "on_disk.kmz"
        with zipfile.ZipFile(str(kmz_path), "w") as z:
            z.writestr("doc.kml", kml_text)

        name, desc, elements = parser.parse_from_file(str(kmz_path))
        assert name == "FromFile"
        assert desc is not None
        assert elements is not None
        # Missing file raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            parser.parse_from_file(str(tmp_path / "nope.kml"))

    def test_kmz_with_multiple_kmls_picks_first(self, tmp_path: Path) -> None:
        """
        Test that when a KMZ archive contains multiple KML files, the XMLKMLParser._extract_kmz
        method extracts and returns the contents of the first KML file found.

        This test creates a KMZ file with two KML files ("a.kml" and "b.kml"), and asserts that the
        extracted content contains a <Document> element, indicating successful extraction.
        """
        # Create KMZ with multiple .kml files and ensure first is chosen
        k1 = '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>A</name></Document></kml>'
        k2 = '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>B</name></Document></kml>'
        kmz_path = tmp_path / "many.kmz"
        with zipfile.ZipFile(str(kmz_path), "w") as z:
            z.writestr("a.kml", k1)
            z.writestr("b.kml", k2)

        extracted = XMLKMLParser._extract_kmz(str(kmz_path))
        assert "<Document>" in extracted

    def test_parse_from_string_other_exception_wrapped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that XMLKMLParser.parse_from_string raises a KMLParseError when an unexpected
        exception (e.g., ValueError) is raised during element extraction.

        This test uses monkeypatch to replace the _extract_all_elements method with one that
        always raises a ValueError, simulating an internal failure. It verifies that the
        parser wraps such exceptions in a KMLParseError.
        """
        parser = XMLKMLParser()

        def raise_value(root: object) -> None:
            raise ValueError("bad")

        monkeypatch.setattr(parser, "_extract_all_elements", raise_value)

        minimal = '<kml xmlns="http://www.opengis.net/kml/2.2"><Document/></kml>'
        with pytest.raises(KMLParseError):
            parser.parse_from_string(minimal)

    def test_extract_kmz_no_kml_file_and_parse_from_file_bad_kmz(self, tmp_path: Path) -> None:
        """
        Test the behavior of XMLKMLParser when handling KMZ files with missing or invalid
        KML content.

        This test covers two scenarios:
        1. Attempting to extract a KMZ file that does not contain any .kml file should raise
            a KMLParseError.
        2. Attempting to parse a file with a .kmz extension that is not a valid ZIP archive
            should also raise a KMLParseError.

        Args:
            tmp_path (Path): Temporary directory provided by pytest for file operations.

        Raises:
            KMLParseError: If the KMZ file does not contain a .kml file or is not a valid
                ZIP archive.
        """
        parser = XMLKMLParser()

        # KMZ with no .kml inside should raise when using file-based extractor
        kmz_no_kml = tmp_path / "nokml.kmz"
        with zipfile.ZipFile(str(kmz_no_kml), "w") as z:
            z.writestr("readme.txt", "hello")

        with pytest.raises(KMLParseError):
            XMLKMLParser._extract_kmz(str(kmz_no_kml))

        # parse_from_file should wrap invalid kmz (not a zip) into KMLParseError
        bad_kmz = tmp_path / "badfile.kmz"
        bad_kmz.write_text("this is not a zip")
        with pytest.raises(KMLParseError):
            parser.parse_from_file(str(bad_kmz))

    def test_extract_document_info_grabs_description(self) -> None:
        """
        Tests that the XMLKMLParser correctly extracts the <name> and <description> elements
        from a KML <Document> and returns them as expected.

        Verifies that:
            - The <name> element is parsed and matches the expected value.
            - The <description> element is parsed and matches the expected value.
        """
        parser = XMLKMLParser()
        kml = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            "<name>N</name><description>Desc</description>"
            "</Document></kml>"
        )

        name, desc, elems = parser.parse_from_string(kml)
        assert name == "N"
        assert desc == "Desc"
        assert elems is not None

    def test_parse_folder_children_appends_various(self) -> None:
        """
        Test that the XMLKMLParser correctly parses a Folder element containing various
        child elements and appends them to the appropriate collections in the Folder
        model instance.

        The test builds a Folder XML element with multiple child types, including
        Placemark (with Point, LineString, Polygon), nested Folder, LineString,
        and Polygon elements. It then parses these children and asserts that the
        Folder model's collections (placemarks, paths, polygons, folders)
        have the expected number of items appended.

        Ensures:
            - At least one Placemark is appended to folder_obj.placemarks.
            - At least two paths (LineString) are appended to folder_obj.paths.
            - At least two polygons are appended to folder_obj.polygons.
            - At least one nested Folder is appended to folder_obj.folders.
        """
        pytest.importorskip("lxml")
        from lxml import etree as _et

        parser = XMLKMLParser()
        # pylint: disable=line-too-long

        # Build a Folder element with various child types
        folder_xml = _et.fromstring(
            '<Folder xmlns="http://www.opengis.net/kml/2.2" id="f">'
            '<Placemark id="p_pt"><Point><coordinates>1,1</coordinates></Point></Placemark>'
            '<Placemark id="p_ls"><LineString><coordinates>2,2 3,3</coordinates></LineString></Placemark>'  # noqa: E501
            '<Placemark id="p_poly"><Polygon><outerBoundaryIs><LinearRing>'
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon></Placemark>"
            '<Folder id="nested"><name>Nested</name></Folder>'
            '<LineString id="ls_s"><coordinates>4,4 5,5</coordinates></LineString>'
            '<Polygon id="poly_s"><outerBoundaryIs><LinearRing>'
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon>"
            "</Folder>"
        )

        # Create an empty Folder model instance
        from kmlorm.models.folder import Folder as FolderModel

        folder_obj = FolderModel(id="f", name="F")

        parser._parse_folder_children(folder_obj, folder_xml)
        # Ensure various collections were appended (Folder model exposes
        # placemarks, folders, paths, polygons)
        assert folder_obj.placemarks.count() >= 1
        assert folder_obj.paths.count() >= 2
        assert folder_obj.polygons.count() >= 2
        assert folder_obj.folders.count() >= 1

    def test_create_functions_except_branches_via_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests the exception handling paths of XMLKMLParser's geometry creation functions
        by monkeypatching constructors to raise exceptions. Ensures that the parser
        returns None when instantiation of Path, Polygon, Point, or MultiGeometry fails.

        Scenarios tested:
        - Path creation from Placemark with a failing constructor.
        - Polygon creation from Placemark and from element with a failing constructor.
        - Point creation from element with a failing constructor.
        - MultiGeometry creation from element with a failing constructor.

        Uses pytest's monkeypatch fixture to replace geometry constructors with a
        class that raises RuntimeError, simulating instantiation failures.
        """
        # Monkeypatch constructors to raise to hit exception handling paths
        parser = XMLKMLParser()
        pytest.importorskip("lxml")
        from lxml import etree as _et

        class BadCtor:  # pylint: disable=too-few-public-methods
            """
            A class whose constructor always raises a RuntimeError to simulate a failure during
            instantiation.

            Raises:
                RuntimeError: Always raised when an instance is created.
            """

            def __init__(self, *args: object, **kwargs: object) -> None:
                raise RuntimeError("ctor fail")

        import kmlorm.parsers.xml_parser as xml_mod

        # Path except branch (from placemark)
        monkeypatch.setattr(xml_mod, "Path", BadCtor)
        placemark = _et.fromstring(
            '<Placemark xmlns="http://www.opengis.net/kml/2.2" id="pp">'
            "<LineString><coordinates>1,2 3,4</coordinates></LineString></Placemark>"
        )
        ls_elem = placemark.find(".//{http://www.opengis.net/kml/2.2}LineString")
        assert parser._create_path_from_placemark(placemark, ls_elem) is None

        # Polygon except branch (placemark)
        monkeypatch.setattr(xml_mod, "Polygon", BadCtor)
        placemark_poly = _et.fromstring(
            '<Placemark xmlns="http://www.opengis.net/kml/2.2" id="pp2">'
            "<Polygon><outerBoundaryIs><LinearRing>"
            "<coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon></Placemark>"
        )
        poly_elem = placemark_poly.find(".//{http://www.opengis.net/kml/2.2}Polygon")
        assert parser._create_polygon_from_placemark(placemark_poly, poly_elem) is None

        # Polygon element except branch
        assert parser._create_polygon_from_element(poly_elem) is None

        # Point except branch
        monkeypatch.setattr(xml_mod, "Point", BadCtor)
        point_elem = _et.fromstring(
            '<Point xmlns="http://www.opengis.net/kml/2.2"><coordinates>9,9</coordinates></Point>'
        )
        assert parser._create_point_from_element(point_elem) is None

        # MultiGeometry except branch
        monkeypatch.setattr(xml_mod, "MultiGeometry", BadCtor)
        mg_elem = _et.fromstring(
            '<MultiGeometry xmlns="http://www.opengis.net/kml/2.2"></MultiGeometry>'
        )
        assert parser._create_multigeometry_from_element(mg_elem) is None

    def test_google_earth_entity_preprocessing(self) -> None:
        """
        Test that XMLKMLParser can handle Google Earth KML with unescaped XML entities.

        This test verifies that:
        - KML with unescaped ampersands in URLs/metadata is parsed successfully
        - The preprocessing method correctly escapes common XML entities
        - Normal KML files continue to work without preprocessing
        """
        parser = XMLKMLParser()

        # KML with unescaped entities (typical Google Earth metadata URL pattern)
        # pylint: disable=line-too-long
        kml_with_unescaped_entities = (
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            "<Document>"
            "<name>Google Earth Test</name>"
            "<description>Testing unescaped entities in metadata URLs</description>"
            "<Placemark>"
            "<name>Test Place</name>"
            "<description>URL with unescaped entities: http://example.com?foo=bar&amp=123&baz=456</description>"  # noqa: E501
            "<Point><coordinates>-122.4194,37.7749,0</coordinates></Point>"
            "</Placemark>"
            "</Document>"
            "</kml>"
        )

        # This should now work because we preprocess Google Earth metadata URLs
        doc_name, doc_description, elements = parser.parse_from_string(kml_with_unescaped_entities)
        assert doc_name == "Google Earth Test"
        assert doc_description is not None
        assert len(elements) > 0

        # Verify the placemark was parsed correctly
        placemark = next((e for e in elements if getattr(e, "name", None) == "Test Place"), None)
        assert placemark is not None
        assert "http://example.com?foo=bar&amp=123&baz=456" in placemark.description

    def test_preprocess_google_earth_entities_method(self) -> None:
        """
        Test the _preprocess_google_earth_entities method directly.

        Verifies that:
        - Unescaped ampersands are properly escaped
        - Already escaped entities are not double-escaped
        - The method handles various entity patterns correctly
        """
        # Test basic entity escaping
        input_text = "URL: http://example.com?foo=bar&baz=123"
        expected = "URL: http://example.com?foo=bar&amp;baz=123"
        result = XMLKMLParser._preprocess_google_earth_entities(input_text)
        assert result == expected

        # Test that already escaped entities are not double-escaped
        input_text = "Already escaped: &amp; &lt; &gt; &quot;"
        result = XMLKMLParser._preprocess_google_earth_entities(input_text)
        assert result == input_text  # Should remain unchanged

        # Test mixed content
        input_text = "Mixed: &amp; and & and more &"
        expected = "Mixed: &amp; and &amp; and more &amp;"
        result = XMLKMLParser._preprocess_google_earth_entities(input_text)
        assert result == expected

    def test_fallback_parsing_preserves_original_error(self) -> None:
        """
        Test that when both normal parsing and preprocessing fail,
        the original parsing error is preserved.
        """
        parser = XMLKMLParser()

        # Completely invalid XML that can't be fixed by entity preprocessing
        invalid_xml = "<kml><Document><name>Bad</name>"  # missing closing tags

        with pytest.raises(KMLParseError) as excinfo:
            parser.parse_from_string(invalid_xml)

        # Should get the original XMLSyntaxError wrapped in KMLParseError
        assert "Invalid XML syntax" in str(excinfo.value)
