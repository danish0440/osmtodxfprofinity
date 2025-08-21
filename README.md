# OSM to DXF Profinity 🗺️➡️📐

A professional OpenStreetMap to AutoCAD DXF converter with a modern web interface. Perfect for architecture students and professionals who need to convert OSM data into CAD-ready drawings.

## ✨ Features

### 🎯 **Architecture-Focused Design**
- **Key Plan Mode**: Simplified drawings for site context (1:2000 scale)
- **Location Plan Mode**: Detailed drawings for site analysis (1:1000 scale)
- **Professional Layer Organization**: Automatic layer creation with proper naming
- **Coordinate Transformation**: WGS84 to Web Mercator projection

### 🌐 **Modern Web Interface**
- **Drag & Drop Upload**: Easy OSM file upload
- **Real-time Progress**: Live conversion tracking
- **Mobile Responsive**: Works on all devices
- **Professional Branding**: Clean, modern design

### 🔧 **Technical Features**
- **High Performance**: PyOsmium for fast OSM parsing
- **Professional Output**: ezdxf for AutoCAD-compatible DXF files
- **Smart Filtering**: Automatic feature selection based on plan type
- **Error Handling**: Robust error management and validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/danish0440/osmtodxfprofinity.git
   cd osmtodxfprofinity
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## 📖 Usage

### Web Interface
1. **Upload OSM File**: Drag and drop your `.osm` file
2. **Choose Plan Type**:
   - **Key Plan**: For site context and orientation
   - **Location Plan**: For detailed site analysis
3. **Convert**: Click convert and wait for processing
4. **Download**: Get your professional DXF file

### Command Line Interface
```bash
# Basic conversion
python osm_to_dxf.py input.osm

# Monochrome output
python osm_to_dxf.py input.osm --no-colors

# Custom projection
python osm_to_dxf.py input.osm --projection EPSG:32633

# Verbose output
python osm_to_dxf.py input.osm --verbose
```

## 🏗️ Perfect for Architecture Students

### Key Plans (1:2000)
- ✅ **Clean Context**: Major roads and buildings only
- ✅ **Monochrome**: Professional black & white output
- ✅ **Street Names**: Essential for orientation
- ✅ **Simplified**: No clutter, perfect for presentations

### Location Plans (1:1000)
- ✅ **Detailed Analysis**: All roads, paths, and features
- ✅ **Colored Output**: Different colors for analysis
- ✅ **Complete Context**: Full site information
- ✅ **CAD Ready**: Proper layers and scaling

## 📁 Project Structure

```
osmtodxfprofinity/
├── app.py                 # Flask web application
├── osm_to_dxf.py         # Core conversion engine
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web interface
├── static/
│   └── logo.png          # Application logo
├── uploads/              # Uploaded OSM files
└── outputs/              # Generated DXF files
```

## 🔧 Technical Details

### Dependencies
- **Flask**: Web framework
- **PyOsmium**: High-performance OSM parsing
- **ezdxf**: Professional DXF file generation
- **pyproj**: Coordinate system transformations
- **Flask-CORS**: Cross-origin resource sharing

### Supported Formats
- **Input**: `.osm`, `.xml` (OpenStreetMap XML)
- **Output**: `.dxf` (AutoCAD Drawing Exchange Format)

### Layer Organization
- **HIGHWAY_MOTORWAY**: Major highways (red)
- **HIGHWAY_PRIMARY**: Primary roads (orange)
- **HIGHWAY_SECONDARY**: Secondary roads (yellow)
- **BUILDING**: Buildings (blue)
- **WATERWAY**: Rivers and streams (cyan)
- **NATURAL**: Parks and green spaces (green)
- **AMENITY**: Points of interest (magenta)

## 🎨 Architecture Workflow

1. **Site Analysis**: Download OSM data for your project site
2. **Key Plan**: Generate simplified context drawing
3. **Location Plan**: Create detailed site analysis
4. **CAD Integration**: Import DXF into AutoCAD/ArchiCAD
5. **Design Development**: Use as base for architectural drawings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- OpenStreetMap contributors for the amazing map data
- PyOsmium team for the high-performance OSM library
- ezdxf developers for the excellent DXF library
- Architecture students who inspired this tool

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/danish0440/osmtodxfprofinity/issues) page
2. Create a new issue with detailed information
3. Include sample OSM files if possible

---

**Made with ❤️ for architecture students and professionals**

*Transform your site analysis workflow with professional OSM to DXF conversion!*