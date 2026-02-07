"""
Core OBF (build file) generator - uses Core_Heat_Processor and Core_Mesh_Processor.
"""
import gzip
import os
import json
import shutil
from datetime import datetime

import numpy as np
import obplib
from scipy.spatial import distance

from .core_heat_processor import Core_Heat_Processor
from .core_mesh_processor import Core_Mesh_Processor

class Core_OBF_Generator:
    """
    Generates OBF (build file) output for EBM: folder structure, JSON manifests,
    and OBP files for start heat, jump safe, postcooling, melt, and ramp operations.
    """

    def __init__(self,project_name_input,base_path,layers,number_of_layers,
                 skip_j,skip_postcooling,pro_start_heat,pro_jump_safe,numb_of_object,
                 project_description,number_of_revision,project_notes,project_material_name,project_powder_size):
        """
        Initialize the OBF generator with project metadata and build options.

        Args:
            project_name_input: Name of the project.
            base_path: Base directory for the build.
            layers: Layer data (e.g. list of per-layer meshes/hatch data).
            number_of_layers: Total number of layers.
            skip_j: Whether to skip jump-safe OBP.
            skip_postcooling: Whether to skip postcooling OBP.
            pro_start_heat: Whether start heat uses pro heat.
            pro_jump_safe: Whether jump safe uses pro heat.
            numb_of_object: Number of objects (for multi-object builds).
            project_description, number_of_revision, project_notes: Project metadata.
            project_material_name: Material name for dependencies.json.
            project_powder_size: Powder size for dependencies.json.
        """
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
        """Store start-heat parameters (algorithm, shape, dimensions, beam, dwell, etc.)."""
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
        """Store jump-safe (pre-heat) parameters: shape, algorithm, dimensions, beam, dwell, repetitions."""
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
        
        

    def init__spatter_safe(self):
        """Placeholder for spatter-safe parameters. No-op."""
        pass
     
        
     
    def init__post_cooling(self,postcooling_shape,postcooling_algorithm,
                           postcooling_length_or_radius,
                             postcooling_jump,postcooling_theta,
                             postcooling_dwell,
                             postcooling_repetitions,
                             postcooling_spot_size_input,
                            postcooling_power_input ):
        """Store postcooling (heat balance) parameters: shape, algorithm, dimensions, beam, dwell, repetitions."""
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
        """Store melt (hatch) parameters: speed, spot size, power, and whether to add connection moves."""
        self.melt_speed=speed
        self.melt_spot_size=spot_size
        self.melt_power=power
        self.melt_connect_or_not=connect_or_not

        

    def init__jason(self,build_piston_distance,powder_piston_dist,
                    recoater_advance_speed,recoater_retract_speed,
                      recoater_dwell_time,recoater_full_repeats,
                      recoater_build_repeats,trigger_start):
        """Store layer-default JSON parameters: piston distances, recoater speeds/dwell/repeats, trigger."""
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
        """
        Create the full OBF output: folder, build processors, manifest/dependencies JSON,
        all OBP files (start heat, jump safe, postcooling, melt, ramp), and buildInfo.json.
        """
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
        """Compute build details: start heat flag, layer count, jump-safe and postcooling flags."""
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
        """Create BuildProcessors folder and copy default build.lua into it."""
        os.makedirs(f"{self.file_name}/BuildProcessors", exist_ok=True)

        os.makedirs(f"{self.file_name}/BuildProcessors/default", exist_ok=True)
        
       # lua_path=self.base_path+'/default_obps/build.lua'
        lua_path=f'{self.software_path}/default_obps/build.lua'
        
        destination_path = f'{self.file_name}/BuildProcessors/default/build.lua'
        # Copy the file
        shutil.copy2(lua_path, destination_path)
        print("build.Lua copied successfully!")
        
    

    
    def create_buildprocessor_jason(self):
        """Write buildProcessors.json that references the default Lua processor."""
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
        """Write manifest.json with project id, name, description, revision, author, reference."""
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
        """Write dependencies.json with material name and powder size."""
        data={"material": {"name": f"{self.material_name}",
    "powderSize": f'{self.powder_size}'
  },"software": {}}
        
        with open(self.file_name+'/dependencies.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        
        print(f"JSON file '{self.file_name}/dependencies.json' has been created successfully!")
        
        


    
    
    
    
    
    def upload_base_obp_file(self):
        """Load the default BseScan.obp file into self.base_scan."""
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.base_scan=obplib.read_obp(main_path+'BseScan.obp')
        print('Uploading Base scan')
 
    
 
    def upload_postcooling_obp_file(self):
        """Load the default HeatBalanceCool.obp file into self.postcooling_def."""
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.postcooling_def=obplib.read_obp(main_path+'HeatBalanceCool.obp')
        print('Uploading Heat balance cool')

    

    def upload_ramp_obp_file(self):
        """Load the default Ramp.obp file into self.ramp."""
        #has number at the end
        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.ramp=obplib.read_obp(main_path+'Ramp.obp')
        print('Uploading ramp')

    
    
    
    
    def upload_ramp_to_base_obp_file(self):
        """Load the default RampDownToBse.obp file into self.ramp_to_base."""
        #has number at the end

        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.ramp_to_base=obplib.read_obp(main_path+'RampDownToBse.obp')
        print('Uploading ramp down to base')
    

    def upload_ramp_pro_obp_file(self):
        """Load the default RampWithProHeat.obp file into self.pro_ramp."""
        #has number at the end

        #main_path=self.base_path+'/default_obps/'
        main_path=f'{self.software_path}/default_obps/'
        self.pro_ramp=obplib.read_obp(main_path+'RampWithProHeat.obp')
        print('Uploading pro ramp')
        


    def upload_default_obp_files(self):
        """Load all default OBP files (base scan, ramp, postcooling, ramp-to-base, ramp-with-pro)."""
        self.upload_base_obp_file()
        
        self.upload_ramp_obp_file()
        
        self.upload_postcooling_obp_file()
        
        self.upload_ramp_to_base_obp_file()
        
        self.upload_ramp_pro_obp_file()
            
        #obplib.write_obp(self.base_scan, "test_for_only.obp")


 
   #****** it need more than this --> somethign like loop
    def create_start_heat_obp(self):
        """Generate StartHeat.obp from the configured start-heat pattern and write it to the OBF obp folder."""
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
        """Generate jump-safe OBP for the given layer number and write Layer{N}jumpsafe.obp."""
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
        """Placeholder for spatter-safe OBP generation. No-op."""
        pass
    
    

    def create_post_cooling_obp(self,layer_numb):
        """Generate postcooling (heat balance) OBP for the given layer and write Layer{N}heatbalance.obp."""
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
        
        """Detect bounding squares for contours in one layer slice; return optimized list of (center_x, center_y, side_length)."""
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
        """
        Order hatch lines for minimal travel (nearest-neighbor) with optional connection segments.

        Args:
            allpoints: Point array.
            separated_lines: List of line segments (point index pairs).
            selected_hatch_spacing: Max distance for inserting connection moves.
            connect_or_not: Whether to add connection segments.

        Returns:
            List of (p1, p2) in optimized order, or None if inconsistent.
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
        """
        Generate melt OBP file(s) for one layer, optionally split by detected objects.

        Args:
            layer_numb: Layer index (for filename).
            layer: PyVista layer data (points/lines) for this layer.
        """
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
        """Write Ramp{i}.obp from the loaded default ramp OBP."""
        obplib.write_obp(self.ramp, f"{self.file_name}/obp/Ramp{i}.obp")
        self.final_ramp.append(f'Ramp{i}.obp')
        
        
    def create_ramp_down_to_base_obps(self,i):
        """Write RampDownToBse{i}.obp from the loaded default ramp-to-base OBP."""
        obplib.write_obp(self.ramp_to_base, f"{self.file_name}/obp/RampDownToBse{i}.obp")
        self.final_ramptobase.append(f'RampDownToBse{i}.obp')
        
    
        
        
    def create_pro_ramp_obps(self,i):
        """Write RampWithProHeat{i}.obp from the loaded default pro-heat ramp OBP."""
        obplib.write_obp(self.pro_ramp, f"{self.file_name}/obp/RampWithProHeat{i}.obp")
        self.final_pro_ramp.append(f'RampWithProHeat{i}.obp')
        

#if one object or mroe different strategy ( for chekcing the llimit)
    def creat_all_obp_files(self):
        """
        Create all OBP files: start heat, jump safe and postcooling per layer,
        melt per layer/object, then default files (BseScan, HeatBalanceCool, ramp variants).
        """
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
        """Gzip every .obp file in the OBF obp folder and remove the original .obp."""
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
        """Build the startHeat section for buildInfo.json (file path, sensor, target temp, timeout)."""
        self.start_heat_jason={     
    "file": "obp/StartHeat.obp.gz",
    "temperatureSensor": "Sensor1",
    "targetTemperature": self.start_heat_target_temp,
    "timeout": 144000
  }

        

    def create_layerDefaults_jason(self):
        """Build the layerDefaults section for buildInfo.json (piston, recoater, trigger)."""
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
        """Build the layers list for buildInfo.json (per-layer jumpSafe, melt, heatBalance OBP references)."""
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
        """Assemble and write buildInfo.json (startHeat, layerDefaults, layers)."""
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
        
