#!/usr/bin/env python3
"""
OSM to DXF Converter
Converts OpenStreetMap data to AutoCAD DXF format with proper layer organization.

Author: OSM to DXF Converter
Version: 1.0.0
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

import osmium
import ezdxf
from ezdxf import colors
from pyproj import Transformer


class OSMNode:
    """Represents an OSM node with coordinates and tags."""
    
    def __init__(self, id: int, lat: float, lon: float, tags: Dict[str, str] = None):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.tags = tags or {}
        self.x = None  # Projected coordinates
        self.y = None


class OSMWay:
    """Represents an OSM way with node references and tags."""
    
    def __init__(self, id: int, nodes: List[int], tags: Dict[str, str] = None):
        self.id = id
        self.nodes = nodes
        self.tags = tags or {}
        self.geometry = []  # Will store projected coordinates


class OSMRelation:
    """Represents an OSM relation with members and tags."""
    
    def __init__(self, id: int, members: List[Tuple[str, int, str]], tags: Dict[str, str] = None):
        self.id = id
        self.members = members  # (type, ref, role)
        self.tags = tags or {}


class LayerMapper:
    """Maps OSM tags to DXF layers with styling."""
    
    def __init__(self, use_colors: bool = True):
        self.layer_config = {
            'highway': {
                'motorway': {'layer': 'HIGHWAY_MOTORWAY', 'color': colors.RED, 'lineweight': 100},
                'trunk': {'layer': 'HIGHWAY_TRUNK', 'color': colors.RED, 'lineweight': 80},
                'primary': {'layer': 'HIGHWAY_PRIMARY', 'color': colors.YELLOW, 'lineweight': 60},
                'secondary': {'layer': 'HIGHWAY_SECONDARY', 'color': colors.CYAN, 'lineweight': 40},
                'tertiary': {'layer': 'HIGHWAY_TERTIARY', 'color': colors.GREEN, 'lineweight': 30},
                'residential': {'layer': 'HIGHWAY_RESIDENTIAL', 'color': colors.WHITE, 'lineweight': 20},
                'service': {'layer': 'HIGHWAY_SERVICE', 'color': colors.GRAY, 'lineweight': 10},
                'footway': {'layer': 'HIGHWAY_FOOTWAY', 'color': colors.MAGENTA, 'lineweight': 5},
                'cycleway': {'layer': 'HIGHWAY_CYCLEWAY', 'color': colors.BLUE, 'lineweight': 5},
                'path': {'layer': 'HIGHWAY_PATH', 'color': colors.GREEN, 'lineweight': 5},
            },
            'building': {
                'default': {'layer': 'BUILDING', 'color': colors.GRAY, 'lineweight': 25}
            },
            'waterway': {
                'river': {'layer': 'WATERWAY_RIVER', 'color': colors.BLUE, 'lineweight': 50},
                'stream': {'layer': 'WATERWAY_STREAM', 'color': colors.BLUE, 'lineweight': 20},
                'canal': {'layer': 'WATERWAY_CANAL', 'color': colors.BLUE, 'lineweight': 30},
                'drain': {'layer': 'WATERWAY_DRAIN', 'color': colors.CYAN, 'lineweight': 10},
            },
            'natural': {
                'water': {'layer': 'NATURAL_WATER', 'color': colors.BLUE, 'lineweight': 25},
                'coastline': {'layer': 'NATURAL_COASTLINE', 'color': colors.BLUE, 'lineweight': 50},
                'tree': {'layer': 'NATURAL_TREE', 'color': colors.GREEN, 'lineweight': 5},
                'forest': {'layer': 'NATURAL_FOREST', 'color': colors.GREEN, 'lineweight': 25},
            },
            'amenity': {
                'default': {'layer': 'AMENITY', 'color': colors.MAGENTA, 'lineweight': 15}
            },
            'landuse': {
                'default': {'layer': 'LANDUSE', 'color': colors.YELLOW, 'lineweight': 15}
            }
        }
    
        self.use_colors = use_colors
    
    def get_layer_info(self, tags: Dict[str, str]) -> Dict[str, any]:
        """Get layer information based on OSM tags."""
        for key, value in tags.items():
            if key in self.layer_config:
                category = self.layer_config[key]
                if value in category:
                    layer_info = category[value].copy()
                    if not self.use_colors:
                        layer_info['color'] = colors.WHITE
                    return layer_info
                elif 'default' in category:
                    layer_info = category['default'].copy()
                    if not self.use_colors:
                        layer_info['color'] = colors.WHITE
                    return layer_info
        
        # Default layer for unmatched features
        default_color = colors.WHITE if self.use_colors else colors.WHITE
        return {'layer': 'OSM_OTHER', 'color': default_color, 'lineweight': 10}


class CoordinateTransformer:
    """Handles coordinate transformation from WGS84 to target projection."""
    
    def __init__(self, target_crs: str = "EPSG:3857"):
        """Initialize transformer. Default is Web Mercator."""
        self.transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
        self.target_crs = target_crs
    
    def transform(self, lon: float, lat: float) -> Tuple[float, float]:
        """Transform WGS84 coordinates to target projection."""
        return self.transformer.transform(lon, lat)


class OSMHandler(osmium.SimpleHandler):
    """OSM data handler using osmium for efficient parsing."""
    
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.nodes = {}
        self.ways = []
        self.relations = []
        self.bounds = None
    
    def node(self, n):
        """Process OSM nodes."""
        tags = dict(n.tags) if n.tags else {}
        node = OSMNode(n.id, n.location.lat, n.location.lon, tags)
        self.nodes[n.id] = node
    
    def way(self, w):
        """Process OSM ways."""
        tags = dict(w.tags) if w.tags else {}
        nodes = [n.ref for n in w.nodes]
        way = OSMWay(w.id, nodes, tags)
        self.ways.append(way)
    
    def relation(self, r):
        """Process OSM relations."""
        tags = dict(r.tags) if r.tags else {}
        members = [(m.type, m.ref, m.role) for m in r.members]
        relation = OSMRelation(r.id, members, tags)
        self.relations.append(relation)


class DXFGenerator:
    """Generates DXF files from OSM data."""
    
    def __init__(self, target_crs: str = "EPSG:3857", use_colors: bool = True):
        self.doc = ezdxf.new('R2010')
        self.msp = self.doc.modelspace()
        self.layer_mapper = LayerMapper(use_colors)
        self.coord_transformer = CoordinateTransformer(target_crs)
        self.created_layers = set()
    
    def create_layer(self, layer_name: str, color: int, lineweight: int):
        """Create a DXF layer with specified properties."""
        if layer_name not in self.created_layers:
            layer = self.doc.layers.new(layer_name)
            layer.color = color
            layer.lineweight = lineweight
            self.created_layers.add(layer_name)
    
    def process_nodes(self, nodes: Dict[int, OSMNode]):
        """Transform node coordinates and create point features for tagged nodes."""
        logging.info(f"Processing {len(nodes)} nodes...")
        
        for node in nodes.values():
            # Transform coordinates
            node.x, node.y = self.coord_transformer.transform(node.lon, node.lat)
            
            # Create point features for nodes with significant tags
            if node.tags and any(key in ['amenity', 'shop', 'tourism', 'highway'] for key in node.tags.keys()):
                layer_info = self.layer_mapper.get_layer_info(node.tags)
                self.create_layer(layer_info['layer'], layer_info['color'], layer_info['lineweight'])
                
                # Create a point or small circle for the node
                self.msp.add_circle(
                    center=(node.x, node.y),
                    radius=5.0,  # 5 meter radius
                    dxfattribs={'layer': layer_info['layer']}
                )
    
    def process_ways(self, ways: List[OSMWay], nodes: Dict[int, OSMNode]):
        """Convert OSM ways to DXF polylines."""
        logging.info(f"Processing {len(ways)} ways...")
        
        for way in ways:
            if not way.tags:
                continue
            
            # Get coordinates for way nodes
            coordinates = []
            for node_id in way.nodes:
                if node_id in nodes:
                    node = nodes[node_id]
                    coordinates.append((node.x, node.y))
            
            if len(coordinates) < 2:
                continue
            
            # Determine layer and styling
            layer_info = self.layer_mapper.get_layer_info(way.tags)
            self.create_layer(layer_info['layer'], layer_info['color'], layer_info['lineweight'])
            
            # Create polyline or polygon
            if way.tags.get('area') == 'yes' or 'building' in way.tags or 'landuse' in way.tags:
                # Create polygon (closed polyline)
                if coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])  # Close the polygon
                
                polyline = self.msp.add_lwpolyline(
                    coordinates,
                    close=True,
                    dxfattribs={'layer': layer_info['layer']}
                )
            else:
                # Create polyline (open)
                polyline = self.msp.add_lwpolyline(
                    coordinates,
                    dxfattribs={'layer': layer_info['layer']}
                )
    
    def save(self, output_path: str):
        """Save the DXF document."""
        self.doc.saveas(output_path)
        logging.info(f"DXF file saved: {output_path}")


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main function to run the OSM to DXF converter."""
    parser = argparse.ArgumentParser(
        description='Convert OpenStreetMap data to AutoCAD DXF format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python osm_to_dxf.py map.osm
  python osm_to_dxf.py map.osm --output map.dxf --projection EPSG:32633
  python osm_to_dxf.py map.osm --verbose
        """
    )
    
    parser.add_argument('input_file', help='Input OSM file path')
    parser.add_argument('-o', '--output', help='Output DXF file path (default: input_file.dxf)')
    parser.add_argument('-p', '--projection', default='EPSG:3857', 
                       help='Target coordinate system (default: EPSG:3857 - Web Mercator)')
    parser.add_argument('--no-colors', action='store_true', help='Generate monochrome DXF (all layers in white)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_path = args.output
    else:
        output_path = input_path.with_suffix('.dxf')
    
    logging.info(f"Converting {input_path} to {output_path}")
    logging.info(f"Target projection: {args.projection}")
    
    try:
        # Parse OSM data
        logging.info("Parsing OSM data...")
        handler = OSMHandler()
        handler.apply_file(str(input_path))
        
        logging.info(f"Parsed {len(handler.nodes)} nodes, {len(handler.ways)} ways, {len(handler.relations)} relations")
        
        # Generate DXF
        logging.info("Generating DXF...")
        use_colors = not args.no_colors
        dxf_gen = DXFGenerator(args.projection, use_colors)
        
        # Process data
        dxf_gen.process_nodes(handler.nodes)
        dxf_gen.process_ways(handler.ways, handler.nodes)
        
        # Save DXF file
        dxf_gen.save(output_path)
        
        logging.info("Conversion completed successfully!")
        logging.info(f"Created {len(dxf_gen.created_layers)} layers")
        
    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
