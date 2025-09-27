# KML 2.2 Specification Reference

## Official Documentation

- **OGC KML 2.2 Standard**: https://www.ogc.org/standards/kml
- **Google Earth KML Reference**: https://developers.google.com/kml/documentation/kmlreference
- **KML Tutorial**: https://developers.google.com/kml/documentation/kml_tut

## Core KML Elements

### Document Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Document Name</name>
    <description>Document Description</description>
    <!-- Content goes here -->
  </Document>
</kml>
```

### Placemark (Point)
```xml
<Placemark>
  <name>Placemark Name</name>
  <description>Description text</description>
  <Point>
    <coordinates>longitude,latitude,altitude</coordinates>
  </Point>
  <ExtendedData>
    <Data name="key">
      <value>value</value>
    </Data>
  </ExtendedData>
</Placemark>
```

### LineString (Path)
```xml
<Placemark>
  <name>Path Name</name>
  <LineString>
    <tessellate>1</tessellate>
    <coordinates>
      lon1,lat1,alt1 lon2,lat2,alt2 lon3,lat3,alt3
    </coordinates>
  </LineString>
</Placemark>
```

### Polygon (Area)
```xml
<Placemark>
  <name>Polygon Name</name>
  <Polygon>
    <extrude>1</extrude>
    <altitudeMode>relativeToGround</altitudeMode>
    <outerBoundaryIs>
      <LinearRing>
        <coordinates>
          lon1,lat1,alt1 lon2,lat2,alt2 lon3,lat3,alt3 lon1,lat1,alt1
        </coordinates>
      </LinearRing>
    </outerBoundaryIs>
    <innerBoundaryIs>
      <LinearRing>
        <coordinates>
          <!-- Hole coordinates -->
        </coordinates>
      </LinearRing>
    </innerBoundaryIs>
  </Polygon>
</Placemark>
```

### Folder (Container)
```xml
<Folder>
  <name>Folder Name</name>
  <description>Folder Description</description>
  <visibility>1</visibility>
  <!-- Child elements go here -->
  <Placemark>...</Placemark>
  <Folder>...</Folder>
</Folder>
```

### NetworkLink (External Reference)
```xml
<NetworkLink>
  <name>Network Link Name</name>
  <Link>
    <href>http://example.com/file.kml</href>
    <refreshMode>onInterval</refreshMode>
    <refreshInterval>3600</refreshInterval>
  </Link>
</NetworkLink>
```

### GroundOverlay (Image Overlay)
```xml
<GroundOverlay>
  <name>Overlay Name</name>
  <Icon>
    <href>http://example.com/image.png</href>
  </Icon>
  <LatLonBox>
    <north>39.5</north>
    <south>39.0</south>
    <east>-76.0</east>
    <west>-76.5</west>
  </LatLonBox>
</GroundOverlay>
```

## Styles

### Style Definition
```xml
<Style id="styleId">
  <IconStyle>
    <color>ff0000ff</color>
    <scale>1.2</scale>
    <Icon>
      <href>http://example.com/icon.png</href>
    </Icon>
  </IconStyle>
  <LineStyle>
    <color>ff00ffff</color>
    <width>4</width>
  </LineStyle>
  <PolyStyle>
    <color>7f00ff00</color>
    <fill>1</fill>
    <outline>1</outline>
  </PolyStyle>
</Style>
```

### StyleMap (Highlighted vs Normal)
```xml
<StyleMap id="styleMapId">
  <Pair>
    <key>normal</key>
    <styleUrl>#normalStyle</styleUrl>
  </Pair>
  <Pair>
    <key>highlight</key>
    <styleUrl>#highlightStyle</styleUrl>
  </Pair>
</StyleMap>
```

## Extended Data

### Simple Data
```xml
<ExtendedData>
  <Data name="fieldName">
    <displayName>Display Name</displayName>
    <value>Field Value</value>
  </Data>
</ExtendedData>
```

### Schema-based Data
```xml
<!-- Schema definition -->
<Schema name="schemaName" id="schemaId">
  <SimpleField type="string" name="fieldName">
    <displayName>Field Display Name</displayName>
  </SimpleField>
</Schema>

<!-- Usage in Placemark -->
<ExtendedData>
  <SchemaData schemaUrl="#schemaId">
    <SimpleData name="fieldName">Field Value</SimpleData>
  </SchemaData>
</ExtendedData>
```

## Time Elements

### TimeStamp
```xml
<TimeStamp>
  <when>2023-01-01T12:00:00Z</when>
</TimeStamp>
```

### TimeSpan
```xml
<TimeSpan>
  <begin>2023-01-01T00:00:00Z</begin>
  <end>2023-12-31T23:59:59Z</end>
</TimeSpan>
```

## Coordinate Systems

- **Default**: WGS84 (EPSG:4326)
- **Format**: longitude,latitude,altitude
- **Longitude**: -180 to 180 degrees
- **Latitude**: -90 to 90 degrees
- **Altitude**: Optional, in meters

## Altitude Modes

- `clampToGround`: Ignore altitude, place on ground
- `relativeToGround`: Altitude relative to ground level
- `absolute`: Altitude relative to sea level

## Common Attributes

- `id`: Unique identifier
- `visibility`: 0 (hidden) or 1 (visible)
- `open`: 0 (closed) or 1 (open) for folders
- `address`: Street address
- `phoneNumber`: Phone number
- `Snippet`: Short description for balloon

## Color Format

Colors are in AABBGGRR hexadecimal format:
- AA: Alpha (transparency)
- BB: Blue component
- GG: Green component
- RR: Red component

Examples:
- `ff0000ff`: Opaque red
- `7f00ff00`: Semi-transparent green
- `ffff0000`: Opaque blue

## Namespace

All KML elements must use the namespace:
```xml
xmlns="http://www.opengis.net/kml/2.2"
```

## File Extensions

- `.kml`: Uncompressed KML file
- `.kmz`: Compressed KML archive (ZIP format)

## Best Practices

1. Always include XML declaration and namespace
2. Use meaningful names and descriptions
3. Keep coordinate precision reasonable (6 decimal places ≈ 10cm accuracy)
4. Close polygons by repeating the first coordinate
5. Use folders to organize related elements
6. Include extended data for rich metadata
7. Consider file size for large datasets

## Implementation Notes for KML ORM

### Supported Elements
- ✅ Placemark (Point)
- ✅ Folder
- 🔄 LineString (in progress)
- 🔄 Polygon (in progress)
- ❌ NetworkLink (planned)
- ❌ GroundOverlay (planned)
- ❌ Styles (planned)

### Coordinate Handling
- Automatically parse longitude, latitude, altitude
- Validate coordinate ranges
- Support multiple input formats (tuple, list, string)
- Calculate distances and bearings

### Query Capabilities
- Django-style filtering (`name__icontains`, etc.)
- Geospatial queries (`near()`, `within_bounds()`)
- Relationship navigation (folder → placemarks)
- Chaining and ordering