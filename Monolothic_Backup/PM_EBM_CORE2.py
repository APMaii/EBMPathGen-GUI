
"""
Created on Tue Feb  4 00:59:21 2025

@author: apm

all things to millimeter

search . and then chekc before that (if )
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

# Read your mesh
#mesh = pv.read("Desktop/slice_plane_7.vtk")



#mesh = pv.read("Desktop/our_final_mesh.vtk")



'''


each mesh is descreibed with a lot of points --> we have mesh.points


each slcie has points. lines

'''




class Core_Mesh_Processor():
    def __init__(self):
        pass

  
    def shapely_to_pyvista(self,shapely_mesh):
        pass
    
    def pyvista_to_shapely(self,pyvista_mesh):
        pass
    
    
    def pyvista_one_slice(self,pyvista_mesh,x,y,z):
        '''
        
        Mesh ---> Slice (points, lines)
        
        '''
        
        if pyvista_mesh is None:
            return None

        slice_plane = pyvista_mesh.slice(normal=[x,y,z], origin=[0, 0, 0.00000000000000001])
        
        return slice_plane
    
    def pyvista_slice_to_shapely_poly(self,slice_plane):
        '''
        Convert PyVista slice to Shapely polygons with proper interior detection
        
        '''
        
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
        '''
        
        get pyvista mesh --> first slice of them and go to comeback quares (with cneetr andlength)
        
        '''
        
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
        '''
        get pyvista mesh --> get abck pyvista slice (points)
        
        '''
        
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
        '''
        
        get pyvista slcie and then return the polydata(points,lines)
        
        
        '''
        
        
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
        
        '''
        it get the pyvista mesh --> list of polydata(has points and lines)

        '''
        
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
        '''
        just created the obp from  liness and points
        
        one layer to obp 
        
        '''
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
        '''
        
        fixe speed, beam , orientation
        '''
        
        
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


#======*****
        
    def one_layer_one_object(self,pyvista_slice,hatch_spacing=1,hatch_angle=1,connect_or_not=False,speed=None,spot_size=0,power=80):
        '''
        
        just for one layer to one obp

        from dictionary we cna do that for each one
        
        
        '''
        
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



        






#*******
    def one_layer_with_limit(self,pyvista_slice,x_high_lim,x_low_lim,y_high_lim,y_low_lim,hatch_spacing=1,hatch_angle=1,connect_or_not=False,speed=None,spot_size=0,power=80):
        '''
        
        just for one layer to one obp

        from dictionary we cna do that for each one
        
        
        '''
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
        '''
        
        just for one layer to one obp

        from dictionary we cna do that for each one
        
        
        '''
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
        
           
           
        
        
        
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
      
import random
import math
#from BESTSTLEBM2 import DEFAULT_BASE_RADIUS
import numpy as np
import math
import random


#DEFAULT_BASE_RADIUS=50
    
class Core_Heat_Processor():
    def __init__(self):
        pass
    
    #others must be none yet
   # def start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_heat_spot_size,start_heat_beam_current,start_heat_dwell_time):
    def old_start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length):

        #if start_heat_shape == 'Circle':

        BASE_RADIUS = start_heat_dimension
        points = []
        
        # Grid boundaries
        step = start_heat_jump_length
        x = -BASE_RADIUS
        raw_grid = []
    
        while x <= BASE_RADIUS:
            y = -BASE_RADIUS
            while y <= BASE_RADIUS:
                if math.sqrt(x**2 + y**2) <= BASE_RADIUS:
                    raw_grid.append((round(x, 4), round(y, 4)))
                y += step
            x += step
    
        if start_heat_algorithm.lower() == "snake":
            # Snake pattern: row-wise zig-zag
            grid_by_rows = {}
            for x, y in raw_grid:
                grid_by_rows.setdefault(round(x, 4), []).append((x, y))
            
            row_keys = sorted(grid_by_rows.keys())
            for i, key in enumerate(row_keys):
                row = sorted(grid_by_rows[key], key=lambda p: p[1])
                if i % 2 == 0:
                    points.extend(row)
                else:
                    points.extend(row[::-1])
    
        elif start_heat_algorithm.lower() == "random":
            # Random pattern: shuffle all valid points
            points = raw_grid[:]
            random.shuffle(points)
    
        else:
            raise ValueError("Unsupported algorithm. Use 'snake' or 'random'.")
    
        #elif for squares
        
        #self.start_heat_points=points
        
        return points

        
    
    '''
    import math
    import random
    
    def generate_circle_points(radius, jump_length, strategy="directional", start_direction="left_to_right"):
        points = []
        step = jump_length
    
        # Create grid of points
        x_start = -radius
        x_end = radius
        y_start = -radius
        y_end = radius
    
        x = x_start
        while x <= x_end:
            y = y_start
            row_points = []
            while y <= y_end:
                # Only add points inside the circle
                if math.sqrt(x**2 + y**2) <= radius:
                    row_points.append((round(x, 4), round(y, 4)))
                y += step
            if row_points:
                points.append(row_points)
            x += step
    
        # Now reorder points based on strategy
        ordered_points = []
    
        if strategy.lower() == "directional":
            # One consistent direction
            if start_direction == "left_to_right":
                for row in points:
                    ordered_points.extend(row)
            elif start_direction == "right_to_left":
                for row in points:
                    ordered_points.extend(row[::-1])
            elif start_direction == "down_to_up":
                # transpose rows to columns
                columns = list(zip(*points))
                for col in columns:
                    ordered_points.extend(col)
            elif start_direction == "up_to_down":
                columns = list(zip(*points))
                for col in columns[::-1]:
                    ordered_points.extend(col)
    
        elif strategy.lower() == "snake":
            # Zigzag: left to right, right to left
            if start_direction in ("left_to_right", "right_to_left"):
                for idx, row in enumerate(points):
                    if (idx % 2 == 0 and start_direction == "left_to_right") or (idx % 2 == 1 and start_direction == "right_to_left"):
                        ordered_points.extend(row)
                    else:
                        ordered_points.extend(row[::-1])
            elif start_direction in ("down_to_up", "up_to_down"):
                columns = list(zip(*points))
                for idx, col in enumerate(columns):
                    if (idx % 2 == 0 and start_direction == "down_to_up") or (idx % 2 == 1 and start_direction == "up_to_down"):
                        ordered_points.extend(col)
                    else:
                        ordered_points.extend(col[::-1])
    
        elif strategy.lower() == "random":
            flat_points = [pt for row in points for pt in row]
            random.shuffle(flat_points)
            ordered_points = flat_points
    
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
        return ordered_points
    
    
    radius = 10
    jump_length = 1
    strategy = "random"  # or "directional" or "random"
    start_direction = "left_to_right"  # or "right_to_left", "down_to_up", "up_to_down"
    start_direction = "right_to_left"  # or "right_to_left", "down_to_up", "up_to_down"
    
    
    points = generate_circle_points(radius, jump_length, strategy, start_direction)
    
    # Now plot to visualize
    import matplotlib.pyplot as plt
    
    xs, ys = zip(*points)
    
    plt.figure(figsize=(6, 6))
    plt.plot(xs, ys, marker='o', linestyle='-' if strategy != 'random' else 'None', markersize=3)
    plt.scatter([0], [0], color='red', label='Center (0,0)')
    plt.title(f"{strategy.capitalize()} Strategy, Start: {start_direction}")
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True)
    plt.legend()
    plt.show()
    '''

    
   
    
   
    
   


    #def start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_heat_spot_size,start_heat_beam_current,start_heat_dwell_time):
    def start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_direction=0):
        """
        Generate points to fill a circular area for EBM (Electron Beam Melting) heat start pattern.
        
        Parameters:
        -----------
        radius : float
            Radius of the circular area to fill
        jump_length : float
            Distance between consecutive points
        strategy : str
            "random" - randomly ordered points from a grid filling the circle
            "single_directional" - points selected in order from one direction
            "snake" - points selected in a snake pattern where end of line connects to start of next
        start_direction : float
            Starting direction angle in degrees (0 is right, 90 is up, etc.)
        
        Returns:
        --------
        list of tuples
            List of (x, y) coordinates that fill the circle in the specified order
            
            
            
        # Example with random strategy
        random_points = generate_points(radius=40, jump_length=2, strategy="random")
        print(f"Random points: {len(random_points)} points generated")
        
        # Example with single directional strategy (0 degrees = right)
        directional_points = generate_points(radius=40, jump_length=2, strategy="single_directional", start_direction=0)
        print(f"Single directional points: {len(directional_points)} points generated")
        
        # Example with snake strategy (90 degrees = up)
        snake_points = generate_points(radius=40, jump_length=3, strategy="snake", start_direction=270)
        print(f"Snake points: {len(snake_points)} points generated")
        
        
        """
        jump_length=start_heat_jump_length
        if jump_length <= 0:
            raise ValueError("Jump length must be positive")
        radius=start_heat_dimension
        if radius <= 0:
            raise ValueError("Radius must be positive")
        
        # Step 1: Create all grid points within the circle
        all_points = self._create_grid_points_in_circle(radius, jump_length)
        strategy=start_heat_algorithm
        # Step 2: Order the points based on strategy
        if strategy == "random":
            return self._order_points_random(all_points)
        elif strategy == "single directional":
            return self._order_points_single_directional(all_points, start_direction)
        elif strategy == "snake":
            return self._order_points_snake(all_points, start_direction)
        else:
            raise ValueError("Unknown strategy. Choose 'random', 'single_directional', or 'snake'")
    
    
    def _create_grid_points_in_circle(self,radius, jump_length):
        """Create a grid of points inside the circle with the specified spacing"""
        points = []
        
        # Create a grid that covers the circle
        grid_size = jump_length
        x_min, x_max = -radius, radius
        y_min, y_max = -radius, radius
        
        # Round to ensure we have a consistent grid
        x_count = int(2 * radius / grid_size) + 1
        y_count = int(2 * radius / grid_size) + 1
        
        x_values = np.linspace(x_min, x_max, x_count)
        y_values = np.linspace(y_min, y_max, y_count)
        
        for x in x_values:
            for y in y_values:
                # Check if point is within circle
                if (x**2 + y**2) <= radius**2:
                    points.append((x, y))
        
        return points
    
    
    def _order_points_random(self,points):
        """Randomly shuffle the points"""
        # Make a copy to avoid modifying the original
        shuffled_points = points.copy()
        random.shuffle(shuffled_points)
        return shuffled_points
    
    
    def _order_points_single_directional(self,points, start_direction_degrees):
        """
        Order points from one direction to another based on start_direction.
        Points in each line are ordered in the same direction.
        """
        # Convert direction to radians
        start_direction = math.radians(start_direction_degrees)
        
        # Calculate direction vector
        direction_x = math.cos(start_direction)
        direction_y = math.sin(start_direction)
        
        # Calculate perpendicular direction for line organization
        perp_direction_x = -direction_y  # Perpendicular vector
        perp_direction_y = direction_x
        
        # Group points into lines perpendicular to the scan direction
        lines = {}
        
        for point in points:
            x, y = point
            
            # Project point onto the perpendicular direction
            # This gives us a value that uniquely identifies which line the point is on
            line_key = round((x * perp_direction_x + y * perp_direction_y) / 0.01) * 0.01
            
            if line_key not in lines:
                lines[line_key] = []
            
            lines[line_key].append(point)
        
        # Sort the lines by their perpendicular coordinate
        sorted_line_keys = sorted(lines.keys())
        
        # For each line, sort points along the direction vector
        ordered_points = []
        
        for line_key in sorted_line_keys:
            line_points = lines[line_key]
            
            # Sort points along the direction vector
            # Project each point onto the direction vector
            line_points.sort(key=lambda p: p[0] * direction_x + p[1] * direction_y)
            
            ordered_points.extend(line_points)
        
        return ordered_points
    
    
    def _order_points_snake(self,points, start_direction_degrees):
        """
        Order points in a snake pattern.
        Points zigzag back and forth in alternating directions.
        """
        # Convert direction to radians
        start_direction = math.radians(start_direction_degrees)
        
        # Calculate direction vector
        direction_x = math.cos(start_direction)
        direction_y = math.sin(start_direction)
        
        # Calculate perpendicular direction for line organization
        perp_direction_x = -direction_y  # Perpendicular vector
        perp_direction_y = direction_x
        
        # Group points into lines perpendicular to the scan direction
        lines = {}
        
        for point in points:
            x, y = point
            
            # Project point onto the perpendicular direction
            # This gives us a value that uniquely identifies which line the point is on
            line_key = round((x * perp_direction_x + y * perp_direction_y) / 0.01) * 0.01
            
            if line_key not in lines:
                lines[line_key] = []
            
            lines[line_key].append(point)
        
        # Sort the lines by their perpendicular coordinate
        sorted_line_keys = sorted(lines.keys())
        
        # For each line, sort points along the direction vector, alternating direction
        ordered_points = []
        
        for i, line_key in enumerate(sorted_line_keys):
            line_points = lines[line_key]
            
            # Sort points along the direction vector
            # Project each point onto the direction vector
            projection_key = lambda p: p[0] * direction_x + p[1] * direction_y
            
            # Alternate direction for each line (snake pattern)
            if i % 2 == 0:
                line_points.sort(key=projection_key)  # Forward direction
            else:
                line_points.sort(key=projection_key, reverse=True)  # Backward direction
            
            ordered_points.extend(line_points)
            

        '''
        
x_all_points=[]
y_all_points=[]

for point in snake_points:
    x_all_points.append(point[0])
    y_all_points.append(point[1])
    
    '''
        return ordered_points
    
    
    
    def jump_safe_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_direction=0):
        """
        Generate points to fill a circular area for EBM (Electron Beam Melting) heat start pattern.
        
        Parameters:
        -----------
        radius : float
            Radius of the circular area to fill
        jump_length : float
            Distance between consecutive points
        strategy : str
            "random" - randomly ordered points from a grid filling the circle
            "single_directional" - points selected in order from one direction
            "snake" - points selected in a snake pattern where end of line connects to start of next
        start_direction : float
            Starting direction angle in degrees (0 is right, 90 is up, etc.)
        
        Returns:
        --------
        list of tuples
            List of (x, y) coordinates that fill the circle in the specified order
            
            
            
        # Example with random strategy
        random_points = generate_points(radius=40, jump_length=2, strategy="random")
        print(f"Random points: {len(random_points)} points generated")
        
        # Example with single directional strategy (0 degrees = right)
        directional_points = generate_points(radius=40, jump_length=2, strategy="single_directional", start_direction=0)
        print(f"Single directional points: {len(directional_points)} points generated")
        
        # Example with snake strategy (90 degrees = up)
        snake_points = generate_points(radius=40, jump_length=3, strategy="snake", start_direction=270)
        print(f"Snake points: {len(snake_points)} points generated")
        
        
        """
        jump_length=start_heat_jump_length
        if jump_length <= 0:
            raise ValueError("Jump length must be positive")
        radius=start_heat_dimension
        if radius <= 0:
            raise ValueError("Radius must be positive")
        
        # Step 1: Create all grid points within the circle
        all_points = self._create_grid_points_in_circle(radius, jump_length)
        strategy=start_heat_algorithm
        # Step 2: Order the points based on strategy
        if strategy == "random":
            return self._order_points_random(all_points)
        elif strategy == "single directional":
            return self._order_points_single_directional(all_points, start_direction)
        elif strategy == "snake":
            return self._order_points_snake(all_points, start_direction)
        else:
            raise ValueError("Unknown strategy. Choose 'random', 'single_directional', or 'snake'")
            
            
            
    def postcooling_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_direction=0):
        """
        Generate points to fill a circular area for EBM (Electron Beam Melting) heat start pattern.
        
        Parameters:
        -----------
        radius : float
            Radius of the circular area to fill
        jump_length : float
            Distance between consecutive points
        strategy : str
            "random" - randomly ordered points from a grid filling the circle
            "single_directional" - points selected in order from one direction
            "snake" - points selected in a snake pattern where end of line connects to start of next
        start_direction : float
            Starting direction angle in degrees (0 is right, 90 is up, etc.)
        
        Returns:
        --------
        list of tuples
            List of (x, y) coordinates that fill the circle in the specified order
            
            
            
        # Example with random strategy
        random_points = generate_points(radius=40, jump_length=2, strategy="random")
        print(f"Random points: {len(random_points)} points generated")
        
        # Example with single directional strategy (0 degrees = right)
        directional_points = generate_points(radius=40, jump_length=2, strategy="single_directional", start_direction=0)
        print(f"Single directional points: {len(directional_points)} points generated")
        
        # Example with snake strategy (90 degrees = up)
        snake_points = generate_points(radius=40, jump_length=3, strategy="snake", start_direction=270)
        print(f"Snake points: {len(snake_points)} points generated")
        
        
        """
        jump_length=start_heat_jump_length
        if jump_length <= 0:
            raise ValueError("Jump length must be positive")
        radius=start_heat_dimension
        if radius <= 0:
            raise ValueError("Radius must be positive")
        
        # Step 1: Create all grid points within the circle
        all_points = self._create_grid_points_in_circle(radius, jump_length)
        strategy=start_heat_algorithm
        # Step 2: Order the points based on strategy
        if strategy == "random":
            return self._order_points_random(all_points)
        elif strategy == "single directional":
            return self._order_points_single_directional(all_points, start_direction)
        elif strategy == "snake":
            return self._order_points_snake(all_points, start_direction)
        else:
            raise ValueError("Unknown strategy. Choose 'random', 'single_directional', or 'snake'")
            
            


#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================
#=====================================================================


from datetime import datetime
import shutil



#maybe it must be child of Core_PM_processor
#check dwell time in 0000
class Core_OBF_Generator:
    
    def __init__(self,project_name_input,base_path,layers,number_of_layers,
                 skip_j,skip_postcooling,pro_start_heat,pro_jump_safe,numb_of_object,
                 project_description,number_of_revision,project_notes,project_material_name,project_powder_size):
        
        
        #-----For create_obf_file function
        self.project_name_input=project_name_input
        self.base_path=base_path
        self.layers=layers
        self.number_of_layers=number_of_layers
        
        
        #---------------------------
        #-----for calculate all details-----
        #-----------------
        
        self.skip_j=skip_j
        self.skip_postcooling=skip_postcooling
        
        self.pro_start_heat=pro_start_heat
        self.pro_jump_safe=pro_jump_safe
        self.number_of_objects=numb_of_object
        
        

        #-----------------
        #------for some jasons
        #------------------
        self.description=project_description
        self.revision_off_all=number_of_revision
        self.notes=project_notes
        self.material_name=project_material_name
        self.powder_size=project_powder_size
            
        
        
    def init__start_heat(self,start_heat_algorithem,start_heat_shape,start_heat_dimension,
                           start_heat_spot_size,start_heat_beam_current,start_heat_target_temp,
                           start_heat_temp_sensor,start_heat_dwell_time,
                           start_heat_jump_length):
        
        self.start_heat_algorithem=start_heat_algorithem

        
        self.start_heat_shape=start_heat_shape
        
        self.start_heat_dimension=start_heat_dimension
        
        self.start_heat_spot_size= start_heat_spot_size
        
        self.start_heat_beam_current=start_heat_beam_current
        
        self.start_heat_target_temp=start_heat_target_temp
        
        self.start_heat_temp_sensor=start_heat_temp_sensor
        
        self.start_heat_dwell_time=start_heat_dwell_time
        
        
        self.start_heat_jump_length=start_heat_jump_length
        
        
    
                               
                               
                               
    def init__jump_safe(self,jump_pixel_shape,jump_pixel_algorithm,
                        jump_pixel_length_or_radius,
                          jump_pixel_jump,jump_pixel_theta,
                          jump_pixel_dwell,jump_pixel_repetitions,
                          jump_pro_heat_enabled,jump_pixel_spot_size_input,
                           jump_pixel_power_input):
        
        self.jump_pixel_shape=jump_pixel_shape
        
        self.jump_pixel_algorithm=jump_pixel_algorithm
        
        self.jump_pixel_length_or_radius=jump_pixel_length_or_radius
        
        self.jump_pixel_jump=jump_pixel_jump
        
        self.jump_pixel_theta=jump_pixel_theta
        
        self.jump_pixel_dwell=jump_pixel_dwell
        
        self.jump_pixel_repetitions=int(jump_pixel_repetitions)
        
        self.jump_pro_heat_enabled=jump_pro_heat_enabled
        
        self.jump_pixel_spot_size_input=jump_pixel_spot_size_input
        
        self.jump_pixel_power_input=jump_pixel_power_input
        
        
        
        
        
        
    def nit__spatter_safe(self):
        pass
     
        
     
    def init__post_cooling(self,postcooling_shape,postcooling_algorithm,
                           postcooling_length_or_radius,
                             postcooling_jump,postcooling_theta,
                             postcooling_dwell,
                             postcooling_repetitions,
                             postcooling_spot_size_input,
                            postcooling_power_input ):
        
        
        self.postcooling_shape=postcooling_shape
        
        self.postcooling_algorithm=postcooling_algorithm
        
        self.postcooling_length_or_radius=postcooling_length_or_radius
        
        self.postcooling_jump=postcooling_jump
        
        self.postcooling_theta=postcooling_theta
        
        self.postcooling_dwell=postcooling_dwell
        
        self.postcooling_repetitions=int(postcooling_repetitions)
        
        self.postcooling_spot_size_input=postcooling_spot_size_input
        
        self.postcooling_power_input=postcooling_power_input

        

    #here we can get space
    #so based on trhe space
    def init__melt(self,speed,spot_size,power,
                     connect_or_not):
        
        
        self.melt_speed=speed
        self.melt_spot_size=spot_size
        self.melt_power=power
        self.melt_connect_or_not=connect_or_not

        
        
        #-----------------
        #------
        #------------------
        
    def init__jason(self,build_piston_distance,powder_piston_dist,
                    recoater_advance_speed,recoater_retract_speed,
                      recoater_dwell_time,recoater_full_repeats,
                      recoater_build_repeats,trigger_start):
        
        
        
        self.build_piston_distance = build_piston_distance
        self.powder_piston_dist =powder_piston_dist
        self.recoater_advance_speed =recoater_advance_speed
        self.recoater_retract_speed = recoater_retract_speed
        self.recoater_dwell_time =recoater_dwell_time
        self.recoater_full_repeats =recoater_full_repeats
        self.recoater_build_repeats =recoater_build_repeats
        self.trigger_start =trigger_start
        #self.start_heat_target_temp =self.start_heat_target_temp
        self.JUMP_SAFE_REPET = self.jump_pixel_repetitions
        self.HEAT_BALANCE_REPET=self.postcooling_repetitions
        
        #self. =
        
        
        
        
        

        

    
    #all thigns must get to this 
    def CREATE_OBF_FILE(self):
        
        self.software_path=os.getcwd()
        
        os.chdir(self.base_path)
        
        now = datetime.now()
        # Format: YY/MM/DD/H
        formatted_time = now.strftime("%y_%m_%d_%H")

        #change the project_name ...
        self.file_name=f"obf_{self.project_name_input.strip().replace(' ','_')}_{formatted_time}"
        #---------CREATE BASE FOLDER NAMED OBF---------------------
        
        os.makedirs(f"{self.file_name}", exist_ok=True)
        
        
        #-----------------Calculate All things----------------------------
        self.calculate_all_DETAILS()
        
        
        
        #----------------------BuildProcessors------------------------------
        self.create_buildprocessor()
        
        self.create_buildprocessor_jason()

        

        #---------manifest.json---------------------
        self.create_manifest_jason()
        
        
        #---------Dependencies.json---------------------
        self.create_dependencies_json()
        
        

        
        #---------OPB files---------------------
        os.makedirs(f"{self.file_name}/obp", exist_ok=True)
        
        
        
        self.creat_all_obp_files()
        
        
        
        
        self.compress_obp_files()
        
        #--------Buildinfo.jason---------
        self.create_buildInfo_json()
        

        
        
        
    
    
    def calculate_all_DETAILS(self):
        
        
        #NOF --> Number of 
        self.NOF_startheat=1
        
        
        if self.pro_start_heat:
            self.has_pro_start_heat=True
        else:
            self.has_pro_start_heat=False
        
        

        numb_layer=0
        for layer in self.layers:
            #if None
            numb_layer=numb_layer+1
            
            
        #layers ---> 
        #self.finalized_slice_n_layers
        #self.number_of_all_hatched_lines
        
        #we can also chekc this
        #as input self.number_of_all_hatched_lines
        self.NOF_layers=self.number_of_layers
        
        
        
        if self.skip_j :
            self.has_Jump_safe=False
            
        else:
            self.has_Jump_safe=True
            
            
        if self.pro_jump_safe:
            self.has_pro_jump_safe=True
        else:
            self.has_pro_jump_safe=False
            
            
            
        #if skip_s:
         #   self.spatter_safe=0
        #
        
        
        
            
        if self.skip_postcooling:
            self.has_postcooling=False
            
        else:
            self.has_postcooling=True
            
        #has no proheat in default
        

              
            
        


    
    
    def create_buildprocessor(self):
        os.makedirs(f"{self.file_name}/BuildProcessors", exist_ok=True)

        os.makedirs(f"{self.file_name}/BuildProcessors/default", exist_ok=True)
        
       # lua_path=self.base_path+'/default_obps/build.lua'
        lua_path=f'{self.software_path}/default_obps/build.lua'
        
        destination_path = f'{self.file_name}/BuildProcessors/default/build.lua'
        # Copy the file
        shutil.copy2(lua_path, destination_path)
        print("build.Lua copied successfully!")
        
    
    
    
    
    
    def create_buildprocessor_jason(self):
        
        data ={ "default": { "type": "lua",
    "entryPoint": "buildProcessors/default/build.lua"
  } }
        

        with open(self.file_name+'/buildProcessors.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        
        print(f"JSON file '{self.file_name}/buildProcessors.json' has been created successfully!")
        
        
        

        

    #self.description
    #self.revision_off_all
    #self.notes
    def create_manifest_jason(self):
        
        data={"formatVersion": "3.0",
  "project": {
    "id": "bfca625b-1782-48df-bd72-5771e5c77351",
    "name": f"{self.file_name}",
    "description": f"{self.description}",
    "revision": {
      "number": f'{int(self.revision_off_all)}',
      "note": f"{self.notes}"
    }
  },"author": {
    "email": "ali.pilehvarmeibody@studenti.polito.it"
  },"reference": {
    "name": "Pixelmelt",
    "uri": "https://beta.eu.pixelmelt.io"
  }
}
        
        


        
        with open(self.file_name+'/manifest.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        
        print(f"JSON file '{self.file_name}/manifest.json' has been created successfully!")
        
        


    #self.material_name
    #self.powder_size
    def create_dependencies_json(self):
        data={"material": {"name": f"{self.material_name}",
    "powderSize": f'{self.powder_size}'
  },"software": {}}
        
        with open(self.file_name+'/dependencies.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        
        print(f"JSON file '{self.file_name}/dependencies.json' has been created successfully!")
        
        


    
    
    
    
    
    def upload_base_obp_file(self):
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.base_scan=obplib.read_obp(main_path+'BseScan.obp')
        print('Uploading Base scan')
 
    
 
    def upload_postcooling_obp_file(self):
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.postcooling_def=obplib.read_obp(main_path+'HeatBalanceCool.obp')
        print('Uploading Heat balance cool')

    

    def upload_ramp_obp_file(self):
        #has number at the end
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.ramp=obplib.read_obp(main_path+'Ramp.obp')
        print('Uploading ramp')

    
    
    
    
    def upload_ramp_to_base_obp_file(self):
        #has number at the end

        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.ramp_to_base=obplib.read_obp(main_path+'RampDownToBse.obp')
        print('Uploading ramp down to base')
    

    def upload_ramp_pro_obp_file(self):
        #has number at the end

        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.pro_ramp=obplib.read_obp(main_path+'RampWithProHeat.obp')
        print('Uploading pro ramp')
        


    def upload_default_obp_files(self):
        
        self.upload_base_obp_file()
        
        self.upload_ramp_obp_file()
        
        self.upload_postcooling_obp_file()
        
        self.upload_ramp_to_base_obp_file()
        
        self.upload_ramp_pro_obp_file()
            
        #obplib.write_obp(self.base_scan, "test_for_only.obp")





 
 
   #****** it need more than this --> somethign like loop
    def create_start_heat_obp(self):
   
        heat_process=Core_Heat_Processor()
        
        points=heat_process.start_heat_generatore_demo(self.start_heat_shape,self.start_heat_dimension,self.start_heat_algorithem,self.start_heat_jump_length)
        
        
        #heat_process=Core_Heat_Processor()
        #points=heat_process.start_heat_generatore_demo('Circle',50000,'random',2000)
        
        #list of tuples
        #each tuples has two numpy array
        
        
        
        x_points=[]
        y_points=[]
        
        for tup in points:
            x_points.append(tup[0])
            y_points.append(tup[1])
            
            
            
       
        
        obp_points=[]

        for x,y in zip(x_points,y_points): 
            obp_points.append(obplib.Point(float(x), float(y)))
            
        
            
        dwell_time=[]
        
        for i in range(0,len(x_points)):
            if i==0:
                #***
                dwell_time.append(int(self.start_heat_dwell_time))
                #dwell_time.append(80000)
                
            else:
                dwell_time.append(0)
                
                
        
        
        beam_params=obplib.Beamparameters( self.start_heat_spot_size, self.start_heat_beam_current)
        
                
        timedpoints=obplib.TimedPoints(obp_points,dwell_time,beam_params)
        
        
        if self.has_pro_start_heat:
            value=True
        else:
            value=False
            
        syncpoints=obplib.SyncPoint('ExternalSync',value,0.0)
        
        final_start_heat_obp=[syncpoints,timedpoints]
        
        
        
        obplib.write_obp(final_start_heat_obp, f"{self.file_name}/obp/StartHeat.obp")
        
        
        
        # Path for gzipped OBP file
        #output_path = f"{self.file_name}/obp/StartHeat.obp.gz"
        
        # Write using gzip if obplib does not auto-handle it
        #with gzip.open(output_path, 'wb') as f:
       #     obplib.write_obp(final_start_heat_obp, f)
    
    
    
        
        
        
        self.final_start_heat_obp.append('StartHeat.obp')
        
        print(f"{self.file_name}/obp/StartHeat.obp")

        



        #now for defaults
        

        
        
        
        
        
        
    #just like start heat we must get
    #also the post cooling is just start heat but no Pro
    #just they must input (i) for each layer building
    
    
    

    
    
    
    #*** also this needs mroe than this
    def create_jump_safe_obp(self,layer_numb):
        
        if self.jump_safe_points:
            pass
        else:
            
        
            heat_process=Core_Heat_Processor()
            self.jump_safe_points=heat_process.jump_safe_generatore_demo(self.jump_pixel_shape.lower(),
                                                          self.jump_pixel_length_or_radius,
                                                          self.jump_pixel_algorithm.lower(),
                                                          self.jump_pixel_jump,
                                                          self.jump_pixel_theta)
        
        
            
        
       # points=heat_process.jump_safe_generatore_demo('circle',
       #                                               50000,
        #                                             'random',
        #                                              2000,
       ##                                               0)
        
        

        #list of tuples
        #each tuples has two numpy array
        
        
        #even these must calculate once ********
        x_points=[]
        y_points=[]
        
        for tup in self.jump_safe_points:
            x_points.append(tup[0])
            y_points.append(tup[1])
            
            

        obp_points=[]

        for x,y in zip(x_points,y_points): 
            obp_points.append(obplib.Point(float(x), float(y)))
            
        
        
        
        
        
            
        dwell_time=[]
        
        for i in range(0,len(x_points)):
            if i==0:
                #***
                dwell_time.append(int(self.jump_pixel_dwell))
                #dwell_time.append(80000)
                
            else:
                dwell_time.append(0)
                
  
        
        beam_params=obplib.Beamparameters( self.jump_pixel_spot_size_input,
                                          self.jump_pixel_power_input)
        
                
        timedpoints=obplib.TimedPoints(obp_points,dwell_time,beam_params)
        
        
        if self.jump_pro_heat_enabled:
            value=True
        else:
            value=False
            
        syncpoints=obplib.SyncPoint('ExternalSync',value,0.0)
        
        
        
        
        final_jump_safe_obp=[syncpoints,timedpoints]
        
        #also repetition for each one
        
       # self.final_jump_safe_obps.append(final_jump_safe_obp)

        obplib.write_obp(final_jump_safe_obp, f"{self.file_name}/obp/Layer{layer_numb}jumpsafe.obp")
        
        self.final_jump_safe_obps.append(f'Layer{layer_numb}jumpsafe.obp')
        
        print(f"{self.file_name}/obp/Layer{layer_numb}jumpsafe.obp")
        



        
        
        
        
        
        
        
    #also we must get 
    def create_spatter_safe_obp(self):
        pass
    
    
    



    
    def create_post_cooling_obp(self,layer_numb):
        
        if self.post_cool_points:
            pass
        else:

            heat_process=Core_Heat_Processor()
            self.post_cool_points=heat_process.postcooling_generatore_demo(self.postcooling_shape.lower(),
                                                            self.postcooling_length_or_radius,
                                                            self.postcooling_algorithm.lower(),
                                                            self.postcooling_jump,
                                                            self.postcooling_theta)
           
       # points=heat_process.jump_safe_generatore_demo('circle',
       #                                               50000,
        #                                             'random',
        #                                              2000,
       ##                                               0)
        
        

        #list of tuples
        #each tuples has two numpy array
        
        
        
        x_points=[]
        y_points=[]
        
        for tup in self.post_cool_points:
            x_points.append(tup[0])
            y_points.append(tup[1])
            
            

        obp_points=[]

        for x,y in zip(x_points,y_points): 
            obp_points.append(obplib.Point(float(x), float(y)))
            
        
        

        
        
            
        dwell_time=[]
        
        for i in range(0,len(x_points)):
            if i==0:
                #***
                dwell_time.append(int(self.postcooling_dwell))
                #dwell_time.append(80000)
                
            else:
                dwell_time.append(0)
                
  
        
        beam_params=obplib.Beamparameters( self.postcooling_spot_size_input,
                                          self.postcooling_power_input)
        
                
        timedpoints=obplib.TimedPoints(obp_points,dwell_time,beam_params)
        
        
        
        
        
        value=False
            
        syncpoints=obplib.SyncPoint('ExternalSync',value,0.0)
        
        
        
        
        final_post_cool_obp=[syncpoints,timedpoints]
        
        #also  #also repetition for each one
        #self.final_post_cool_obps.append(final_post_cool_obp)
        
        
        
        obplib.write_obp(final_post_cool_obp, f"{self.file_name}/obp/Layer{layer_numb}heatbalance.obp")
        self.final_post_cool_obps.append(f'Layer{layer_numb}heatbalance.obp')
        
        print(f'Layer{layer_numb}heatbalance.obp')
        
            


    def object_detection_limit(self,one_layer):
        
         squares=[]
        
         contours = one_layer.split_bodies()
         
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
             
         pm_processor=Core_Mesh_Processor()
         optimized_square=pm_processor.optimize_squares(squares, 20)
        
         return optimized_square

             



    def optimize_lines_with_order_in_layer(self,allpoints, separated_lines,selected_hatch_spacing,connect_or_not=False):
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
                        if distance.euclidean(allpoints[last_line[1]],allpoints[next_line[0]]) <= selected_hatch_spacing +1:
                            
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
            
    def create_melt_for_multi_objects(self,layer_numb,layer):
        n_objects=self.number_of_objects
        
        
        
        value=False
        syncpoints=obplib.SyncPoint('ExternalSync',value,0.0)       

        final_obp_lines=[syncpoints]

        
        square=self.object_detection_limit(layer)

        if n_objects==1:

            all_points=layer.points.tolist()
            opt_lines=layer.lines
            
            beam_params=obplib.Beamparameters(self.melt_spot_size,self.melt_power)

            
            
            
            #pm_processor=Core_Mesh_Processor()
            #obp_lines=pm_processor.layer_to_obp_file(whole_points,whole_lines,self.melt_speed,self.melt_spot_size,self.melt_power)


            point_index_lists = []
            
            i = 0
            
            while i < len(opt_lines):
                num_points = opt_lines[i]
                point_indices = opt_lines[i+1:i+1+num_points]
                point_index_lists.append(point_indices)
                i += 1 + num_points  # Move to the next line block
                
                
            obp_lines=[]
            
            for line in point_index_lists:
                obp_lines.append(obplib.Line(obplib.Point(all_points[line[0]][0], all_points[line[0]][1]),  obplib.Point(all_points[line[1]][0], all_points[line[1]][1]), int(self.melt_speed),beam_params))


                 
            final_obp_lines.extend(obp_lines)
            number=100
            
            obplib.write_obp(final_obp_lines, f"{self.file_name}/obp/Layer{layer_numb}Object{number}melt.obp")

            self.final_melt_obps.append(f'Layer{layer_numb}Object{number}melt.obp')
            
            print(f'{self.file_name}/obp/Layer{layer_numb}Object{number}melt.obp')
            
       
        
        
            
            
            
            
        else:
        
            for j in range(0,n_objects):
                center_x=square[0][0]
                center_y=square[0][1]
                side_length=square[0][2]
                half_side=side_length/2
                
                x_high_lim=max(center_x + half_side , center_x - half_side)
                x_low_lim=min(center_x + half_side , center_x - half_side)
                
                y_high_lim=max(center_y + half_side , center_y - half_side)
                y_low_lim=min(center_y + half_side , center_y - half_side)
                
                
                #pm_processor=Core_Mesh_Processor()
    
                whole_points=layer.points
                whole_lines=layer.lines
                
                
                    
                
                mask = (
                    (whole_points[:, 0] >= x_low_lim) & (whole_points[:, 0] <= x_high_lim) &
                    (whole_points[:, 1] >= y_low_lim) & (whole_points[:, 1] <= y_high_lim)
                )
                filtered_points = whole_points[mask]
                
                
                
                # Step 3: Map old indices to new indices
                # Get the indices of points that passed the filter
                old_indices = np.where(mask)[0]
                
                # Create a mapping from old index to new index
                index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(old_indices)}
                
                
                #??????????????
                # Step 4: Filter and remap lines
                filtered_lines = []
                '''
                for line in whole_lines:
                    num_points = line[0]
                    point_indices = line[1:1 + num_points]
                
                    # Check if all point indices in this line are in the filtered points
                    if all(idx in index_map for idx in point_indices):
                        # Remap the point indices to new filtered indices
                        new_indices = [index_map[idx] for idx in point_indices]
                        filtered_lines.append([num_points] + new_indices)
                '''
                
                i=0
                while i < len(whole_lines):
                    num_points = whole_lines[i]
                    point_indices = whole_lines[i+1:i+1- + num_points]
                
                    # Check if all point indices in this line are in the filtered points
                    if all(idx in index_map for idx in point_indices):
                        # Remap the point indices to new filtered indices
                        new_indices = [index_map[idx] for idx in point_indices]
                        filtered_lines.append([num_points] + new_indices)
                    i += 1 +num_points
                    
                    
                    
                '''
                    
                #---------
                #here we must get the hatchign space only
                optimized_filtered_lines=self.optimize_lines_with_order_in_layer(filtered_points,whole_lines,self.hatching_space ,self.melt_connect_or_not)
                #then only optimzied lines not filtered
                obp_lines=[]
                
                for line in new_indices:
                    obp_lines.append(obplib.Line(obplib.Point(filtered_points[optimized_filtered_lines[0]][0], filtered_points[optimized_filtered_lines[0]][1]),  obplib.Point(filtered_points[optimized_filtered_lines[1]][0], filtered_points[optimized_filtered_lines[1]][1]), int(self.melt_speed),beam_params))

                
                '''

                
                obp_lines=[]
                
                for line in new_indices:
                    obp_lines.append(obplib.Line(obplib.Point(filtered_points[filtered_lines[0]][0], filtered_points[filtered_lines[0]][1]),  obplib.Point(filtered_points[filtered_lines[1]][0], filtered_points[filtered_lines[1]][1]), int(self.melt_speed),beam_params))

                
                

                
                #optimized_lines=pm_processor.optimize_lines_with_order_in_layer(filtered_points,filtered_lines,connect_or_not=self.melt_connect_or_not)
                #obp_lines=pm_processor.layer_to_obp_file(filtered_points,optimized_lines,self.melt_speed,self.melt_spot_size,self.melt_power)
    

                
                
                final_obp_lines.extend(obp_lines)
                number=100+j
                
                obplib.write_obp(final_obp_lines, f"{self.file_name}/obp/Layer{layer_numb}Object{number}melt.obp")
    
                self.final_melt_obps.append(f'Layer{layer_numb}Object{number}melt.obp')
                
                print(f'Layer{layer_numb}Object{number}melt.obp')
            
                
                
                
                
            
    def create_ramp_obps(self,i):
        obplib.write_obp(self.ramp, f"{self.file_name}/obp/Ramp{i}.obp")
        self.final_ramp.append(f'Ramp{i}.obp')
        
        
    def create_ramp_down_to_base_obps(self,i):
        obplib.write_obp(self.ramp_to_base, f"{self.file_name}/obp/RampDownToBse{i}.obp")
        self.final_ramptobase.append(f'RampDownToBse{i}.obp')
        
    
        
        
    def create_pro_ramp_obps(self,i):
        obplib.write_obp(self.pro_ramp, f"{self.file_name}/obp/RampWithProHeat{i}.obp")
        self.final_pro_ramp.append(f'RampWithProHeat{i}.obp')
        
    
    
    
#if one object or mroe different strategy ( for chekcing the llimit)
    def creat_all_obp_files(self):
        #also create Buildinfo here
        
        
        #*********
        #start heat and jump safge must be multiple and a lot of
        
        
        #------STARTHEAT------------
        self.final_start_heat_obp=[]
        
        self.create_start_heat_obp()
        



        
        self.jump_safe_points=None
        self.final_jump_safe_obps=[]
        #len ()--> the number of this 
        for i,jump_layer in enumerate(self.layers):
            
            self.create_jump_safe_obp(i+1)
            
            
        
        
        
        
        
        self.post_cool_points=None
        self.final_post_cool_obps=[]
        
        for i,postcool in enumerate(self.layers):
            
            self.create_post_cooling_obp(i+1)
        
        
        
        
        self.NOF_Generated_Layers=0
        #first chekc if one is ok , mroe sya more
        self.final_melt_obps=[]
        for i,layer in  enumerate(self.layers):
            self.create_melt_for_multi_objects(i+1,layer)
            self.NOF_Generated_Layers=self.NOF_Generated_Layers+1
        
        
        self.upload_default_obp_files()
        
        self.final_uploaded_files=[]
        
        obplib.write_obp(self.base_scan, f"{self.file_name}/obp/BseScan.obp")
        
        self.final_uploaded_files.append('BseScan.obp')

        
        obplib.write_obp(self.postcooling_def, f"{self.file_name}/obp/HeatBalanceCool.obp")
        #self.final_uploaded_files.append('Postcool.obp') ---> No need
        
        
        
        #ramp--> for each layer --> 1 ,2,3,4,5..
        #also we have 
        
        self.final_ramp=[]
        self.final_ramptobase=[]
        self.final_pro_ramp=[]
        
        #for layer in layers:
        for i in range(1,self.NOF_Generated_Layers+1):
            self.create_ramp_obps(i)
            self.create_ramp_down_to_base_obps(i)
            
            if self.has_pro_jump_safe or self.has_pro_start_heat:
                self.create_pro_ramp_obps(i)
                
            
        
            
        

    def compress_obp_files(self):
        for filename in os.listdir(f'{self.file_name}/obp'):
            if filename.endswith('.obp'):
                obp_path = os.path.join(f'{self.file_name}/obp', filename)
                gz_path = obp_path + '.gz'
    
                # Compress the .obp file
                with open(obp_path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
    
                # Delete the original .obp file
                os.remove(obp_path)
    
        print(f"All .obp files in '{self.file_name}/obp'' have been compressed and original files deleted.")
    
        



        
    def create_start_heat_jason(self):
        self.start_heat_jason={     
    "file": "obp/StartHeat.obp.gz",
    "temperatureSensor": "Sensor1",
    "targetTemperature": self.start_heat_target_temp,
    "timeout": 144000
  }

        
            

    def create_layerDefaults_jason(self):
        
        self.layer_default_jason= {
      "buildPistonDistance": self.build_piston_distance,
      "powderPistonDistance": self.powder_piston_dist,
      "recoaterAdvanceSpeed":self.recoater_advance_speed ,
      "recoaterRetractSpeed":self.recoater_retract_speed ,
      "recoaterDwellTime": self.recoater_dwell_time,
      "recoaterFullRepeats": self.recoater_full_repeats,
      "recoaterBuildRepeats":self.recoater_build_repeats ,
      "triggeredStart": self.trigger_start
    }
        
        
    def create_melt_layer_jason(self):
        #finally it must return List
        self.final_layer_list=[]
        
        
        
        for i,layer in enumerate(self.layers):
            this_layer={}

            
            if self.has_Jump_safe:
                this_layer['jumpSafe']=[]
                this_layer['jumpSafe'].append({'file': '/obp/'+self.final_jump_safe_obps[i]+'.gz' , 'repetitions':self.JUMP_SAFE_REPET  })
                
                
            this_layer['melt']=[]
            if self.has_pro_jump_safe or self.has_pro_start_heat:
                this_layer['melt'].append({'file':'/obp/'+self.final_pro_ramp[i]+'.gz' , 'repetitions':40})
                

            this_layer['melt'].append({'file':'/obp/'+self.final_ramp[i]+'.gz' , 'repetitions':40})
                
            
            #for i in .. if layer= i+1 
            #so just for this layer we must get ...
            for j in range(self.number_of_objects):
                number=i* self.number_of_objects + j 
                 
                this_layer['melt'].append({'file':'/obp/'+self.final_melt_obps[number]+'.gz' , 'repetitions':1})
                
                
                
            
            
            
            this_layer['melt'].append({'file':'/obp/'+self.final_ramptobase[i]+'.gz' , 'repetitions':40})
            
            
            this_layer['melt'].append({'file':'/obp/BseScan.obp/'+'.gz' , 'repetitions':1})


            if self.has_postcooling:
                this_layer['heatBalance']=[]
                this_layer['heatBalance'].append({'file':'/obp/'+self.final_post_cool_obps[i]+'.gz' , 'repetitions':self.HEAT_BALANCE_REPET})
                
                
            
            self.final_layer_list.append(this_layer)
            
                





    def create_buildInfo_json(self):
        #first start heat
        self.create_start_heat_jason()
        self.create_layerDefaults_jason()
        self.create_melt_layer_jason()
        
        
        #self.start_heat_jason
        #self.layer_default_jason
        #self.final_layer_list
        
        
        
        
        build_info_dict={"startHeat":self.start_heat_jason  ,
                         'layerDefaults':self.layer_default_jason ,
                         'layers':   self.final_layer_list    }

        with open(self.file_name+'/buildInfo.json', 'w', encoding='utf-8') as json_file:
            json.dump(build_info_dict, json_file, indent=4, ensure_ascii=False)
        
        print(f"JSON file '{self.file_name}/buildInfo.json' has been created successfully!")
        
        
        
'''       

# Load the data
with open("/Users/apm/Desktop/final_layers.pkl", "rb") as f:
    final_layers = pickle.load(f)




with open("/Users/apm/Desktop/obf_config_test.json", "r") as f:
    config = json.load(f)
    
    
    
    
    

obf_generator = Core_OBF_Generator(
    config["project"]["name"],
    config["project"]["folder_path"],
    final_layers,
    config["hatching"]["number_of_lines"],
    False,  # j_pixel_skip_is
    False,  # postcooling_pixel_skip_is
    config["start_heat"]["enabled"],
    config["jump_safe"]["enabled"],
    1,  # numb_object_based_on_squares
    config["project"]["description"],
    config["project"]["revision_number"],
    config["project"]["notes"],
    config["project"]["material"],
    config["project"]["powder_size"]
)

obf_generator.init__start_heat(
    config["start_heat"]['algorithm'],
    config["start_heat"]['shape'],
    config["start_heat"]['dimension'],
    config["start_heat"]['spot_size'],
    config["start_heat"]['beam_current'],
    config["start_heat"]['target_temp'],
    config["start_heat"]['temp_sensor'],
    config["start_heat"]['dwell_time'],
    config["start_heat"]['jump_length']
)
obf_generator.init__jump_safe(
   config["jump_safe"]['shape'],
   config["jump_safe"]['algorithm'],
   config["jump_safe"]['length_or_radius'],
   config["jump_safe"]['jump'],
   config["jump_safe"]['theta'],
   config["jump_safe"]['dwell'],
   config["jump_safe"]['repetitions'],
   config["jump_safe"]['enabled'],
   config["jump_safe"]['spot_size'],
   config["jump_safe"]['power']
)

obf_generator.init__post_cooling(
    config["post_cooling"]['shape'],
    config["post_cooling"]['algorithm'],
    config["post_cooling"]['length_or_radius'],
    config["post_cooling"]['jump'],
    config["post_cooling"]['theta'],
    config["post_cooling"]['dwell'],
    config["post_cooling"]['repetitions'],
    config["post_cooling"]['spot_size'],
    config["post_cooling"]['power']

)
    
obf_generator.init__melt(
    config["melt"]['speed'],
    config["melt"]['spot_size'],
    config["melt"]['power'],
    config["melt"]['connection']
    
)

obf_generator.init__jason(
    config["jason"]['build_piston_distance'],
    config["jason"]['powder_piston_distance'],
    config["jason"]['recoater_advance_speed'],
    config["jason"]['recoater_retract_speed'],
    config["jason"]['recoater_dwell_time'],
    config["jason"]['recoater_full_repeats'],
    config["jason"]['recoater_build_repeats'],
    config["jason"]['triggered_start']
)

obf_generator.CREATE_OBF_FILE()


#AttributeError: 'Core_OBF_Generator' object has no attribute 'base_scan'



for layer in final_layers:
    
    layer=final_layers[0]
    final_obp_lines=[]
    pm_processor=Core_Mesh_Processor()

    whole_points=layer.points
    whole_lines=layer.lines

    #obp_lines=pm_processor.layer_to_obp_file(whole_points,whole_lines,100,200,300)
    opt_lines=whole_lines
    all_points=whole_points.tolist()
    #all_points=allpoints
    beam_params=obplib.Beamparameters(200, 300)
    
    obp_lines=[]
    
    point_index_lists = []
    
    i = 0
    
    while i < len(opt_lines):
        num_points = opt_lines[i]
        point_indices = opt_lines[i+1:i+1+num_points]
        point_index_lists.append(point_indices)
        i += 1 + num_points  # Move to the next line block
        
        
    obp_lines=[]
    
    for line in point_index_lists:
        obp_lines.append(obplib.Line(obplib.Point(all_points[line[0]][0], all_points[line[0]][1]),  obplib.Point(all_points[line[1]][0], all_points[line[1]][1]), 1000,beam_params))


        
         
         
    final_obp_lines.extend(obp_lines)
    number=100
    
   # obplib.write_obp(final_obp_lines, f"{self.file_name}/obp/Layer{layer_numb}Object{number}melt.obp")
    
    
    
'''
    
 
    
    
    

        