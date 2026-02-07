
"""
Created on Tue Feb  4 00:59:21 2025

@author: apm

"""
import gzip
import numpy as np
import json
import os   
import obplib 
import pickle
from scipy.spatial import distance
#
import pyvista as pv
import trimesh
from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.ops import unary_union
import svgwrite
from shapely.geometry import MultiPoint
import pyvista as pv

class Core_Mesh_Processor():
    """
    Mesh processing for EBM path generation: slicing, hatching, geometry conversion,
    and OBP layer generation from PyVista/Shapely geometry.
    """

    def __init__(self):
        """Initialize the mesh processor. No parameters required."""
        pass

  
    def shapely_to_pyvista(self,shapely_mesh):
        """Convert a Shapely geometry to a PyVista mesh. Placeholder for future implementation."""
        pass
    
    def pyvista_to_shapely(self,pyvista_mesh):
        """Convert a PyVista mesh to Shapely geometry. Placeholder for future implementation."""
        pass
    
    
    def pyvista_one_slice(self,pyvista_mesh,x,y,z):
        """
        Extract a single slice from a PyVista mesh with the given plane normal and origin.

        Args:
            pyvista_mesh: PyVista mesh to slice.
            x, y, z: Components of the slice plane normal vector.

        Returns:
            PyVista PolyData slice, or None if the mesh is None.
        """
        if pyvista_mesh is None:
            return None

        slice_plane = pyvista_mesh.slice(normal=[x,y,z], origin=[0, 0, 0.00000000000000001])
        
        return slice_plane
    
    def pyvista_slice_to_shapely_poly(self,slice_plane):
        """
        Convert a PyVista slice to Shapely polygon(s) with proper interior detection.

        Args:
            slice_plane: PyVista PolyData representing a planar slice.

        Returns:
            Shapely Polygon or MultiPolygon, or None on failure or if no valid polygons.
        """
        try:
            # Get all cells from the slice plane
            polygons = []
            
            # Get unique cells that form closed loops
            edges = []
            for i in range(slice_plane.n_cells):
                cell = slice_plane.get_cell(i)
                points = cell.points[:, :2]  # Get only X,Y coordinates
                edges.append((points[0], points[1]))
            
            # Use polygonize to create proper polygons from edges
            lines = [LineString(edge) for edge in edges]
            merged_lines = unary_union(lines)
            polygons = list(polygonize(merged_lines))
            
            if not polygons:
                print("No valid polygons found")
                return None
                
            # Create a multipolygon if we have multiple polygons
            if len(polygons) > 1:
                return MultiPolygon(polygons)
            else:
                return polygons[0]
                
        except Exception as e:
            print(f"Error in convert_slice_to_shapely: {str(e)}")
            return None
        
    def calculate_overlap_percentage(self,square1, square2):
        """
        Calculate the overlap percentage between two squares.
        
        Parameters:
        - square1, square2: Tuples of (center_x, center_y, side_length)
        
        Returns:
        - float: Overlap percentage relative to the smaller square's area
        """
        x1, y1, s1 = square1
        x2, y2, s2 = square2
        
        # Calculate the intersection rectangle
        x_left = max(x1 - s1/2, x2 - s2/2)
        y_bottom = max(y1 - s1/2, y2 - s2/2)
        x_right = min(x1 + s1/2, x2 + s2/2)
        y_top = min(y1 + s1/2, y2 + s2/2)
        
        # Check if squares overlap
        if x_right > x_left and y_top > y_bottom:
            intersection_area = (x_right - x_left) * (y_top - y_bottom)
            smaller_square_area = min(s1 * s1, s2 * s2)
            return (intersection_area / smaller_square_area) * 100
        return 0
    
    def merge_squares(self,square1, square2):
        """
        Merge two squares into one that encompasses both.
        
        Parameters:
        - square1, square2: Tuples of (center_x, center_y, side_length)
        
        Returns:
        - tuple: New square (center_x, center_y, side_length)
        """
        x1, y1, s1 = square1
        x2, y2, s2 = square2
        
        # Find the extremes of both squares
        left = min(x1 - s1/2, x2 - s2/2)
        right = max(x1 + s1/2, x2 + s2/2)
        bottom = min(y1 - s1/2, y2 - s2/2)
        top = max(y1 + s1/2, y2 + s2/2)
        
        # Calculate new square parameters
        new_side = max(right - left, top - bottom)
        new_center_x = (left + right) / 2
        new_center_y = (bottom + top) / 2
        
        return (new_center_x, new_center_y, new_side)
    
    def optimize_squares(self,squares, overlap_threshold=20):
        """
        Optimize squares by merging overlapping ones and removing contained squares.
        
        Parameters:
        - squares: List of (center_x, center_y, side_length)
        - overlap_threshold: Percentage threshold for merging squares
        
        Returns:
        - list: Optimized squares
        """
        if not squares:
            return []
        
        # Sort squares by area (largest first)
        squares = sorted(squares, key=lambda x: x[2]**2, reverse=True)
        
        # First pass: remove completely contained squares
        i = 0
        while i < len(squares):
            j = i + 1
            while j < len(squares):
                # Check if square j is contained within square i
                overlap = self.calculate_overlap_percentage(squares[i], squares[j])
                if overlap > 95:  # Using 95% as threshold for "completely contained"
                    squares.pop(j)
                else:
                    j += 1
            i += 1
        
        # Second pass: merge overlapping squares
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(squares):
                j = i + 1
                while j < len(squares):
                    overlap = self.calculate_overlap_percentage(squares[i], squares[j])
                    if overlap > overlap_threshold:
                        # Merge squares i and j
                        new_square = self.merge_squares(squares[i], squares[j])
                        squares.pop(j)
                        squares[i] = new_square
                        changed = True
                    else:
                        j += 1
                i += 1
        
        return squares
        
       
        
    def object_detection(self,pyvista_mesh,overlap_threshold=20):
        """
        Detect bounding squares (center and side length) for each contour in the first slice of the mesh.

        Args:
            pyvista_mesh: PyVista mesh to analyze.
            overlap_threshold: Percentage overlap above which squares are merged (default 20).

        Returns:
            List of tuples (center_x, center_y, side_length) for each optimized bounding square.
        """
        one_slice=self.pyvista_one_slice(pyvista_mesh,0,0,1)
        squares = []
        
        # Get bounds for each separate contour in the mesh
        contours = pyvista_mesh.split_bodies()
        
        #i think ---> it msut be this ---->
        contours = one_slice.split_bodies()

        
        
        
        
        for contour in contours:
            # Get only x and y coordinates
            points = contour.points[:, :2]
            
            # Calculate bounds
            min_x, max_x = np.min(points[:, 0]), np.max(points[:, 0])
            min_y, max_y = np.min(points[:, 1]), np.max(points[:, 1])
            
            # Calculate square parameters
            side_length = max(max_x - min_x, max_y - min_y)
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            squares.append((center_x, center_y, side_length))
            
        return self.optimize_squares(squares, overlap_threshold)
    
    
    
    
    def pyvista_slicer(self,pyvista_mesh,layer_interval=None,n_layers=None):
        """
        Slice a PyVista mesh into horizontal layers along Z.

        Args:
            pyvista_mesh: PyVista mesh to slice.
            layer_interval: Spacing between slice planes (optional).
            n_layers: Number of layers (optional). Exactly one of layer_interval or n_layers must be set.

        Returns:
            Tuple of (slice_planes, n_layers, layer_height, number_of_successive_layer,
            number_of_failed_geom, number_of_failed_slice, failed_slice_id).
        """
        bounds = pyvista_mesh.bounds
        z_min = bounds[4]
        z_max = bounds[5]
        
        slice_planes=[]
        number_of_failed_geom=0
        number_of_successive_layer=0
        number_of_failed_slice=0
        failed_slice_id=[]
        
        

        if layer_interval is not None:
            layer_height=layer_interval
            heights = np.arange(z_min, z_max + layer_interval,layer_interval)
            n_layers=int((z_max - z_min) /layer_interval)+ 1
                                 
                                 
            #for adjustmentsss
            offset=layer_interval/1000000000000
            heights[0] = z_min + offset
            heights[-1] = z_max - offset
            
            
        elif n_layers is not None:
            layer_height = (z_max - z_min) / n_layers
            
            
            heights = np.linspace(z_min, z_max, n_layers)
            offset=layer_height/1000000000000
            heights[0] = z_min + offset
            heights[-1] = z_max - offset
            
            
            
        iii=0
        for height in heights:
            slice_plane = pyvista_mesh.slice(normal=[0, 0, 1], origin=[0, 0, height])
            #and here is not ok
            if slice_plane:
                if slice_plane.n_points > 0:

                    slice_planes.append(slice_plane)

                geometry = self.pyvista_slice_to_shapely_poly(slice_plane)
                if geometry is None:
                    number_of_failed_geom=number_of_failed_geom+1
                    failed_slice_id.append(iii)
                    continue
                else:
                    number_of_successive_layer=number_of_successive_layer+1
  
            else:
                failed_slice_id.append(iii)
                number_of_failed_slice=number_of_failed_slice+1
            iii=iii+1
            
            
            
        return slice_planes, n_layers ,layer_height,number_of_successive_layer,number_of_failed_geom,number_of_failed_slice,failed_slice_id

        





    def pyvista_slice_linear_hatcher(self,pyvista_slice,spacing,angle):
        """
        Generate linear hatch lines for a single PyVista slice at the given spacing and angle.

        Args:
            pyvista_slice: PyVista PolyData slice (planar).
            spacing: Distance between hatch lines.
            angle: Hatch angle in degrees.

        Returns:
            PyVista PolyData with points and lines representing the hatch pattern, or None if invalid.
        """
        if pyvista_slice is None or pyvista_slice.n_points == 0:
            return None

        
        # Convert to Shapely with proper interior detection
        geometry = self.pyvista_slice_to_shapely_poly(pyvista_slice)
        if geometry is None:
            return None
        
        minx, miny, maxx, maxy = geometry.bounds
        
        # Calculate parameters
        width = maxx - minx
        height = maxy - miny
        diagonal = np.sqrt(width**2 + height**2)
        
        angle_rad = np.radians(angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        # Calculate number of lines needed
        num_lines = int(diagonal / spacing) + 2
        
        # Generate hatch lines
        hatch_lines = []
        
        for i in range(-num_lines, num_lines):
            offset = i * spacing
            
            # Create a line that spans the entire geometry
            if abs(cos_angle) > 1e-10:
                x1 = minx - height * abs(sin_angle)
                y1 = offset / cos_angle
                x2 = maxx + height * abs(sin_angle)
                y2 = offset / cos_angle
            else:
                x1 = offset
                y1 = miny - width * abs(cos_angle)
                x2 = offset
                y2 = maxy + width * abs(cos_angle)
            
            # Create and rotate line
            line_start = np.array([x1, y1])
            line_end = np.array([x2, y2])
            
            rotation_matrix = np.array([
                [cos_angle, -sin_angle],
                [sin_angle, cos_angle]
            ])
            
            rotated_start = rotation_matrix @ line_start
            rotated_end = rotation_matrix @ line_end
            
            line = LineString([rotated_start, rotated_end])
            
            # Intersect with the geometry
            intersection = line.intersection(geometry)
            
            if not intersection.is_empty:
                if intersection.geom_type == 'MultiLineString':
                    hatch_lines.extend(list(intersection.geoms))
                elif intersection.geom_type == 'LineString':
                    hatch_lines.append(intersection)
        
        
        # Convert back to PyVista format
        points = []
        lines = []
        point_count = 0
        
        for line in hatch_lines:
            coords = list(line.coords)
            # Add Z coordinate back
            points.extend([[x, y, pyvista_slice.center[2]] for x, y in coords])
            lines.append([len(coords)] + list(range(point_count, point_count + len(coords))))
            point_count += len(coords)
        
        
        
        if points:
            points = np.array(points)
            lines = np.array(lines)
            hatch_polydata = pv.PolyData(points, lines=lines)
            return hatch_polydata
        else:
            return None



    def pyvista_mesh_linear_hatcher(self,pyvista_mesh,spacing,angle,layer_interval=None,n_layers=None,just_show=False):
        """
        Generate linear hatch patterns for all layers of a PyVista mesh.

        Args:
            pyvista_mesh: PyVista mesh to hatch.
            spacing: Hatch line spacing.
            angle: Hatch angle in degrees.
            layer_interval: Layer spacing (optional).
            n_layers: Number of layers (optional).
            just_show: If True, return also raw hatched polydata and line lists for visualization.

        Returns:
            If just_show is False: (whole_points, whole_lines, number_of_failed_hatch_line).
            If just_show is True: (all_hatched_lines, whole_points, whole_lines, number_of_failed_hatch_line).
        """
        all_hatched_lines=[]
        
        
        number_of_failed_hatch_line=0
        
        failed_hatch_id=[]
        
        #also here it can back the tuple 
        
        if layer_interval is not None:
            pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,layer_interval=layer_interval)
        
        elif n_layers is not None:
            pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,n_layers=n_layers)
        
        
        ii=0
        for slicee in pyvista_slices:
            hatched_lines=self.pyvista_slice_linear_hatcher(slicee,spacing,angle)
            if hatched_lines is None:
                
                all_hatched_lines.append(None)
                number_of_failed_hatch_line=number_of_failed_hatch_line+1
                failed_hatch_id.append(ii)
            else:
                all_hatched_lines.append(hatched_lines)
            ii=ii+1

                
          #all_hatched_lines -->list of polydatass that each one has lines and points

        whole_points=[]
        whole_lines=[]
        
        #har layer yek polydasta hast
        
        for layer in all_hatched_lines:
            separated_lines = []
            
            # Initialize a pointer to iterate through the 'lines' array
            i = 0
            
            # Iterate through the 'lines' array
            #while i < len(layer):
            while i < len(layer.lines):  
                num_points = layer.lines[i]  # Get the number of points for the current line
                line_points = layer.lines[i+1:i+1+num_points]  # Get the actual points (skip the number)
                separated_lines.append(line_points)  # Add the line to the result
                i += num_points + 1  # Move to the next group (next number + points)
                
            whole_points.append(layer.points)
            whole_lines.append(separated_lines)
            

        if just_show==True:
            return all_hatched_lines,whole_points,whole_lines,number_of_failed_hatch_line
            
        else:
            return whole_points,whole_lines,number_of_failed_hatch_line
        
            
        '''
        
        #then the hatched lines go to better seperation
        separated_lines = []
        
        # Initialize a pointer to iterate through the 'lines' array
        i = 0
        
        # Iterate through the 'lines' array
        while i < len(all_hatched_lines):
            
            num_points = all_hatched_lines[i]  # Get the number of points for the current line
            line_points = all_hatched_lines[i+1:i+1+num_points]  # Get the actual points (skip the number)
            separated_lines.append(line_points)  # Add the line to the result
            i += num_points + 1  # Move to the next group (next number + points)
        

        return separated_lines,number_of_failed_hatch_line
      '''


        
    def optimize_lines_with_order_in_layer(self,allpoints, separated_lines,connect_or_not=False):
        """
        Order hatch lines for minimal travel by visiting nearest-neighbor lines.

        Args:
            allpoints: Array of points (one per vertex index).
            separated_lines: List of line segments, each as indices into allpoints.
            connect_or_not: If True, insert short connection segments between lines when within spacing.

        Returns:
            List of (p1, p2) index tuples in optimized order, or None if the result is inconsistent.
        """
        remaining_lines = set(range(len(separated_lines)))  #this is set 0 1 2 3 4 5 6 .. len(sperated lines)
        optimized_lines = []
        
        current_line_index = 0
        remaining_lines.remove(current_line_index) #in mishe 1 2 3 4 5 6
        optimized_lines.append(tuple(int(i) for i in separated_lines[current_line_index])) #indexe 0 e sperated tro mide be optimzied

        number_off_connection_lines=0
        
        
        while remaining_lines:
            last_line=optimized_lines[-1]
            p1=int(last_line[0])
            p2=int(last_line[1])
            
            
            # Find the nearest line by comparing all points of current line to other lines
            min_dist = float("inf")
            next_line_index = None
            next_line = None

            for line_index in remaining_lines:
                specific_lines = separated_lines[line_index]
                q1=int(specific_lines[0])
                q2=int(specific_lines[1])
                

                # Calculate distances between endpoints and find the closest configuration
                d1 = distance.euclidean(allpoints[p2], allpoints[q1])  # Current -> Start of next
                d2 = distance.euclidean(allpoints[p2], allpoints[q2])  # Current -> End of next

                if d1 < min_dist:
                    min_dist = d1
                    next_line_index = line_index
                    next_line = (q1, q2)
                if d2 < min_dist:
                    min_dist = d2
                    next_line_index = line_index
                    next_line = (q2, q1)  # Swap endpoints for optimal order

            # Move to the next closest line
            if next_line_index is not None:
                
               
                if connect_or_not==True:
                    if last_line is None:
                        pass
                    else:
                        if distance.euclidean(allpoints[last_line[1]],allpoints[next_line[0]]) <= self.selected_hatch_spacing +1:
                            
                            number_off_connection_lines=number_off_connection_lines+1
                            connect_lines=(last_line[1],next_line[0])
                            optimized_lines.append(connect_lines)
                        else:
                            pass
                        
                    last_line=next_line
                    
                    
                optimized_lines.append(next_line)

                remaining_lines.remove(next_line_index)
                
        if connect_or_not==True:
            
            if len(optimized_lines)==len(separated_lines)+number_off_connection_lines:
                return optimized_lines
            
            else:
                return None
            
        else:
            if len(optimized_lines)==len(separated_lines):
                
                return optimized_lines
            else:
                return None
            
    
    
    def layer_to_obp_file(self,allpoints,alllines,speed,spot_size,power):
        """
        Convert one layer of points and optimized lines to OBP (beam path) line objects.

        Args:
            allpoints: Array of (x, y) or (x, y, z) points.
            alllines: List of (p1, p2) index pairs for each segment.
            speed: Beam speed for the layer.
            spot_size: Beam spot size.
            power: Beam power.

        Returns:
            List of obplib.Line objects for the layer.
        """
        opt_lines=alllines
        all_points=allpoints.tolist()
        #all_points=allpoints
        beam_params=obplib.Beamparameters(spot_size, power)
        
        obp_points=[]
        obp_lines=[]
        for line in opt_lines:

            obp_lines.append(obplib.Line(obplib.Point(all_points[line[0]][0], all_points[line[0]][1]),  obplib.Point(all_points[line[1]][0], all_points[line[1]][1]), speed,beam_params))
            
        return obp_lines
    
    
    
    
    
    def simple_one(self,pyvista_mesh,slice_n_layer=None,slice_layer_interval=None,hatch_spacing=1,hatch_angle=1,connect_or_not=False,speed=None,spot_size=0,power=80):
        """
        Process a full mesh: slice, hatch all layers with fixed speed/beam/orientation, and output OBP lines per layer.

        Args:
            pyvista_mesh: PyVista mesh.
            slice_n_layer: Number of layers (optional).
            slice_layer_interval: Layer height (optional).
            hatch_spacing: Hatch line spacing.
            hatch_angle: Hatch angle in degrees.
            connect_or_not: Whether to add connection moves between lines.
            speed, spot_size, power: Beam parameters for OBP output.

        Returns:
            List of OBP line lists, one per layer.
        """
        '''
        if slice_n_layer is not None:
            slice_planes, n_layers ,layer_height,number_of_successive_layer,number_of_failed_geom,number_of_failed_slice,failed_slice_id=self.pyvista_slicer(pyvista_mesh,n_layers=slice_n_layer)

        elif slice_layer_interval is not None:
             
            slice_planes, n_layers ,layer_height,number_of_successive_layer,number_of_failed_geom,number_of_failed_slice,failed_slice_id= self.pyvista_slicer(pyvista_mesh,layer_interval=slice_layer_interval)
            
        '''
        
        
        if slice_n_layer is not None:
            whole_points,whole_lines,number_of_failed_hatch_line=self.pyvista_mesh_linear_hatcher(pyvista_mesh,spacing=hatch_spacing,angle=hatch_angle,n_layers=slice_n_layer)
        
        elif slice_layer_interval is not None:
            whole_points,whole_lines,number_of_failed_hatch_line=self.pyvista_mesh_linear_hatcher(pyvista_mesh,spacing=hatch_spacing,angle=hatch_angle,layer_interval=slice_layer_interval)
            
            

        #whole points yek liste #--> in yek liste az har layer ke numpye
        
        #whoel poinmt ham ye liste
        #we need all points for this ???
        obp_lines_list=[]
        for i in range(0,len(whole_lines)):
            
            optimized_lines=self.optimize_lines_with_order_in_layer(whole_points[i],whole_lines[i],connect_or_not=connect_or_not)
            

            obp_lines=self.layer_to_obp_file(whole_points[i],optimized_lines,speed,spot_size,power)
            obp_lines_list.append(obp_lines)
        
        
            #obp_lines.write_obp('name') #somethign like f'layer_{i}'
        return obp_lines_list



        
    def one_layer_one_object(self,pyvista_slice,hatch_spacing=1,hatch_angle=1,connect_or_not=False,speed=None,spot_size=0,power=80):
        """
        Generate OBP lines for a single slice (one layer, one object) with given hatch and beam parameters.

        Args:
            pyvista_slice: PyVista slice PolyData.
            hatch_spacing, hatch_angle: Hatch pattern parameters.
            connect_or_not: Whether to add connection segments.
            speed, spot_size, power: Beam parameters.

        Returns:
            List of obplib.Line objects for this layer.
        """
        layer=self.pyvista_slice_linear_hatcher(pyvista_slice,spacing=hatch_spacing,angle=hatch_angle)
        
        
        hatch_lines=layer.lines

        #har layer yek polydasta hast

        separated_lines = []
        
        # Initialize a pointer to iterate through the 'lines' array
        i = 0
        
        # Iterate through the 'lines' array
        #while i < len(layer):
        while i < len(hatch_lines):  
            num_points = hatch_lines[i]  # Get the number of points for the current line
            line_points = hatch_lines[i+1:i+1+num_points]  # Get the actual points (skip the number)
            separated_lines.append(line_points)  # Add the line to the result
            i += num_points + 1  # Move to the next group (next number + points)
            
 
        whole_points=layer.points
        whole_lines=separated_lines
        
        
        
        #self.optimize_lines_with_order_in_layer
        
        optimized_lines=self.optimize_lines_with_order_in_layer(whole_points,whole_lines,connect_or_not=connect_or_not)
        

        obp_lines=self.layer_to_obp_file(whole_points,optimized_lines,speed,spot_size,power)
        
        return obp_lines
        #also it can save that         
   
 

    def all_layers(self,pyvista_mesh,hatch_spacing_list=[],hatch_angle_list=[],connect_or_not_list=[],speed_list=[],spot_size_list=[],power_list=[],layer_interval=None,n_layers=None):
        """
        Process all layers of a mesh with per-layer hatch and beam parameters (list of values per layer).

        Args:
            pyvista_mesh: PyVista mesh.
            hatch_spacing_list, hatch_angle_list, connect_or_not_list: Per-layer hatch options.
            speed_list, spot_size_list, power_list: Per-layer beam parameters.
            layer_interval: Layer height (optional).
            n_layers: Number of layers (optional).
        """
        if layer_interval is not None:
            pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,layer_interval=layer_interval)

        elif n_layers is not None:
           pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,n_layers=n_layers)


        #erach pyvista_slcies has points
        #for one layer , for each object
        obp_lines_for_each_layer=[]
        
        for i in (0,len(pyvista_slices)):
            obp=self.one_layer_one_object(pyvista_slices[i],hatch_spacing=hatch_spacing_list[i],
                                          hatch_angle=hatch_angle_list[i],connect_or_not=connect_or_not_list[i],
                                          speed=speed_list[i],spot_size=spot_size_list[i],power=power_list[i])
            
            
            #save for that layer


    def one_layer_with_limit(self,pyvista_slice,x_high_lim,x_low_lim,y_high_lim,y_low_lim,hatch_spacing=1,hatch_angle=1,connect_or_not=False,speed=None,spot_size=0,power=80):
        """
        Generate OBP lines for one slice restricted to a rectangular XY bounding box.

        Args:
            pyvista_slice: PyVista slice.
            x_high_lim, x_low_lim, y_high_lim, y_low_lim: Bounding box in XY.
            hatch_spacing, hatch_angle, connect_or_not, speed, spot_size, power: Hatch and beam parameters.

        Returns:
            List of obplib.Line objects for the clipped layer.
        """
        points=pyvista_slice.points
        
        
        filtered_points = points[
            (points[:, 0] >= x_low_lim) & (points[:, 0] <= x_high_lim) & 
            (points[:, 1] >= y_low_lim) & (points[:, 1] <= y_high_lim)
        ]
        
        
        
        poly_data = pv.PolyData(filtered_points)
        

        layer=self.pyvista_slice_linear_hatcher(poly_data,spacing=hatch_spacing,angle=hatch_angle)
        

        hatch_lines=layer.lines
        
        
        #har layer yek polydasta hast

        separated_lines = []
        
        # Initialize a pointer to iterate through the 'lines' array
        i = 0
        
        # Iterate through the 'lines' array
        #while i < len(layer):
        while i < len(hatch_lines):  
            num_points = hatch_lines[i]  # Get the number of points for the current line
            line_points = hatch_lines[i+1:i+1+num_points]  # Get the actual points (skip the number)
            separated_lines.append(line_points)  # Add the line to the result
            i += num_points + 1  # Move to the next group (next number + points)
            
 
        whole_points=layer.points
        whole_lines=separated_lines
        
 
        optimized_lines=self.optimize_lines_with_order_in_layer(whole_points,whole_lines,connect_or_not=connect_or_not)
        

        obp_lines=self.layer_to_obp_file(whole_points,optimized_lines,speed,spot_size,power)
        
        return obp_lines
        
        
        
        
        
        
    def all_objects(self,pyvista_mesh,hatch_spacing_list=[],hatch_angle_list=[],connect_or_not_list=[],speed_list=[],spot_size_list=[],power_list=[],layer_interval=None,n_layers=None):
        """
        Process mesh by detected objects: slice, then for each layer and each object apply per-object hatch/beam parameters.

        Args:
            pyvista_mesh: PyVista mesh.
            hatch_spacing_list, hatch_angle_list, connect_or_not_list, speed_list, spot_size_list, power_list: Per-object lists.
            layer_interval: Layer height (optional).
            n_layers: Number of layers (optional).
        """
        #we can say teh threshold basedd on space
        square=self.object_detection(pyvista_mesh)
        n_objects=len(square)
        
        
        if layer_interval is not None:
            pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,layer_interval=layer_interval)

        elif n_layers is not None:
           pyvista_slices,*_=self.pyvista_slicer(pyvista_mesh,n_layers=n_layers)


        for i in (0,len(pyvista_slices)):
            #erach pyvista_slcies has points
            #for one layer , for each object
            obp_lines_for_each_layer=[]
            
            
            for j in range(0,n_objects):
                center_x=square[0][0]
                center_y=square[0][1]
                side_length=square[0][2]
                half_side=side_length/2
                
                x_high_lim=max(center_x + half_side , center_x - half_side)
                x_low_lim=min(center_x + half_side , center_x - half_side)
                
                y_high_lim=max(center_y + half_side , center_y - half_side)
                y_low_lim=min(center_y + half_side , center_y - half_side)
                
                
                
                #we need obp of that 
                #pyvista_slices[0].points
                obp_lines=self.one_layer_with_limit(pyvista_slices[i],x_high_lim,
                                          x_low_lim,y_high_lim,
                                          y_low_lim,
                                          hatch_spacing=hatch_spacing_list[j],
                                          hatch_angle=hatch_angle_list[j],
                                          connect_or_not=connect_or_not_list[j],
                                          speed=speed_list[j],
                                          spot_size=spot_size_list[j],
                                          power=power_list[j])
                
                obp_lines_for_each_layer.append(obp_lines)

            #koel obp_lines ro writer konim to obp
            #layer_obp=[]
            #for i obp_lines_for_each_layer:
                #layer_obp.extend(obp_lines)

