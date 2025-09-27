# Google KML Extensions (gx namespace)

## Official Documentation

- **Google KML Extensions Reference**: https://developers.google.com/kml/documentation/kmlreference#kmlextensions
- **Google Earth KML**: https://developers.google.com/kml/documentation/
- **gx namespace**: `xmlns:gx="http://www.google.com/kml/ext/2.2"`

## Namespace Declaration

Google KML files typically include multiple namespaces:

```xml
<kml xmlns="http://www.opengis.net/kml/2.2"
     xmlns:gx="http://www.google.com/kml/ext/2.2"
     xmlns:kml="http://www.opengis.net/kml/2.2"
     xmlns:atom="http://www.w3.org/2005/Atom">
```

## Extended Geometry Types

### gx:Track (GPS Tracks)
```xml
<gx:Track>
  <altitudeMode>absolute</altitudeMode>
  <gx:interpolate>1</gx:interpolate>
  <when>2023-01-01T10:00:00Z</when>
  <when>2023-01-01T10:01:00Z</when>
  <when>2023-01-01T10:02:00Z</when>
  <gx:coord>-122.0 37.0 50</gx:coord>
  <gx:coord>-122.001 37.001 55</gx:coord>
  <gx:coord>-122.002 37.002 60</gx:coord>
  <ExtendedData>
    <gx:SimpleArrayData name="speed">
      <gx:value>10.5</gx:value>
      <gx:value>12.3</gx:value>
      <gx:value>8.7</gx:value>
    </gx:SimpleArrayData>
  </ExtendedData>
</gx:Track>
```

### gx:MultiTrack (Multiple Track Segments)
```xml
<gx:MultiTrack>
  <altitudeMode>absolute</altitudeMode>
  <gx:interpolate>1</gx:interpolate>
  <gx:Track>
    <!-- First track segment -->
  </gx:Track>
  <gx:Track>
    <!-- Second track segment -->
  </gx:Track>
</gx:MultiTrack>
```

## Animation and Tours

### gx:Tour (Guided Tours)
```xml
<gx:Tour>
  <name>My Tour</name>
  <description>A guided tour of locations</description>
  <gx:Playlist>
    <gx:FlyTo>
      <gx:duration>3.0</gx:duration>
      <gx:flyToMode>smooth</gx:flyToMode>
      <LookAt>
        <longitude>-122.0</longitude>
        <latitude>37.0</latitude>
        <altitude>0</altitude>
        <heading>0</heading>
        <tilt>0</tilt>
        <range>1000</range>
      </LookAt>
    </gx:FlyTo>
    <gx:Wait>
      <gx:duration>2.0</gx:duration>
    </gx:Wait>
    <gx:AnimatedUpdate>
      <gx:duration>5.0</gx:duration>
      <Update>
        <targetHref/>
        <Change>
          <Placemark targetId="placemark1">
            <visibility>1</visibility>
          </Placemark>
        </Change>
      </Update>
    </gx:AnimatedUpdate>
  </gx:Playlist>
</gx:Tour>
```

### gx:TourControl
```xml
<gx:TourControl>
  <gx:playMode>pause</gx:playMode>  <!-- play, pause -->
</gx:TourControl>
```

## Extended Data Types

### gx:SimpleArrayData
```xml
<ExtendedData>
  <gx:SimpleArrayData name="heartrate">
    <gx:value>180</gx:value>
    <gx:value>178</gx:value>
    <gx:value>175</gx:value>
  </gx:SimpleArrayData>
</ExtendedData>
```

## Camera and View Extensions

### gx:ViewerOptions
```xml
<gx:ViewerOptions>
  <gx:option name="historicalimagery" enabled="1"/>
  <gx:option name="sunlight" enabled="1"/>
  <gx:option name="streetview" enabled="1"/>
</gx:ViewerOptions>
```

### gx:horizFov (Camera Field of View)
```xml
<Camera>
  <longitude>-122.0</longitude>
  <latitude>37.0</latitude>
  <altitude>100</altitude>
  <heading>0</heading>
  <tilt>45</tilt>
  <roll>0</roll>
  <gx:horizFov>60</gx:horizFov>
</Camera>
```

## Altitude Modes

### gx:altitudeMode (Extended Altitude Modes)
```xml
<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>
<!-- Values: relativeToSeaFloor, clampToSeaFloor -->
```

## Balloon and Style Extensions

### gx:balloonVisibility
```xml
<gx:balloonVisibility>1</gx:balloonVisibility>
```

### gx:drawOrder (Overlay Z-order)
```xml
<GroundOverlay>
  <gx:drawOrder>1</gx:drawOrder>
  <!-- Higher numbers appear on top -->
</GroundOverlay>
```

## Time Extensions

### gx:TimeStamp and gx:TimeSpan
```xml
<gx:TimeStamp>
  <when>2023-01-01T12:00:00Z</when>
</gx:TimeStamp>

<gx:TimeSpan>
  <begin>2023-01-01T00:00:00Z</begin>
  <end>2023-12-31T23:59:59Z</end>
</gx:TimeSpan>
```

## Cascading Style Sheets

### gx:CascadingStyle
```xml
<gx:CascadingStyle kml:id="cascadingStyle">
  <kml:Style>
    <kml:PolyStyle>
      <kml:color>7f00ff00</kml:color>
    </kml:PolyStyle>
  </kml:Style>
</gx:CascadingStyle>
```

## Phonetic Names

### gx:phonetic
```xml
<name>Tokyo</name>
<gx:phonetic>TOH-kee-oh</gx:phonetic>
```

## Google Earth Specific Features

### Standard Google Earth Styles
Google Earth uses predefined styles and icons:

```xml
<!-- Yellow pushpin (most common) -->
<styleUrl>#ylw-pushpin</styleUrl>

<!-- Other common Google icons -->
<Icon>
  <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
</Icon>
<Icon>
  <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
</Icon>
<Icon>
  <href>http://maps.google.com/mapfiles/kml/paddle/red-stars.png</href>
</Icon>
```

### StyleMaps (Normal/Highlight pairs)
```xml
<StyleMap id="msn_ylw-pushpin">
  <Pair>
    <key>normal</key>
    <styleUrl>#sn_ylw-pushpin</styleUrl>
  </Pair>
  <Pair>
    <key>highlight</key>
    <styleUrl>#sh_ylw-pushpin</styleUrl>
  </Pair>
</StyleMap>
```

### hotSpot (Icon anchor point)
```xml
<IconStyle>
  <Icon>
    <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
  </Icon>
  <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
```

## Common Google Earth Patterns

### Generated by Google Earth
Google Earth typically generates:
- Document name: Often generic like "KmlFile"
- Multiple StyleMaps for normal/highlight states
- Specific icon URLs pointing to Google's servers
- Precise hotSpot definitions for icon alignment
- Standard color formats (AABBGGRR hex)

### Extended Data Patterns
```xml
<!-- Google Earth often uses simple Data elements -->
<ExtendedData>
  <Data name="description">
    <value>User-entered description</value>
  </Data>
</ExtendedData>
```

## Implementation Considerations for KML ORM

### Namespace Handling
- Support multiple namespaces in parsing
- Distinguish between standard KML and gx extensions
- Handle mixed namespace usage

### Google-specific Elements
- Parse gx:Track as specialized geometry type
- Support Google Earth StyleMaps
- Handle Google icon URLs and hotSpots
- Process gx:SimpleArrayData for time-series data

### Backward Compatibility
- Gracefully handle gx elements not yet supported
- Maintain standard KML compatibility
- Parse but preserve unknown gx elements

### Extension Support Roadmap
- ✅ Standard KML 2.2 elements
- 🔄 Google StyleMaps and Icons (in progress)
- ❌ gx:Track and GPS data (planned)
- ❌ gx:Tour and animations (future)
- ❌ gx:SimpleArrayData (planned)

## Testing with Google Earth Files

Google Earth KML files are excellent for testing because they:
- Use real-world coordinate data
- Include complex styling and icons
- Mix standard and extension elements
- Follow Google's specific formatting conventions
- Test edge cases and namespace handling

## References

- [Google KML Extension Reference](https://developers.google.com/kml/documentation/kmlreference#kmlextensions)
- [OGC KML 2.2 vs Google Extensions](https://developers.google.com/kml/documentation/kmlreference#differences)
- [Google Earth Icon Reference](https://kml4earth.appspot.com/icons.html)
- [KML Namespace Handling](https://developers.google.com/kml/documentation/kmlreference#namespace)