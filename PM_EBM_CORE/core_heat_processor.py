import random
import math
import numpy as np
import math
import random

    
class Core_Heat_Processor():
    """
    Generates point patterns for EBM thermal operations: start heat, jump safe, and postcooling.
    Supports circular regions with snake or random ordering.
    """

    def __init__(self):
        """Initialize the heat processor. No parameters required."""
        pass
    
    #others must be none yet
   # def start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length,start_heat_spot_size,start_heat_beam_current,start_heat_dwell_time):
    def old_start_heat_generatore_demo(self,start_heat_shape,start_heat_dimension, start_heat_algorithm, start_heat_jump_length):
        """
        Legacy demo: generate (x, y) points filling a circular region with snake or random order.

        Args:
            start_heat_shape: Shape descriptor (e.g. 'Circle').
            start_heat_dimension: Radius of the circle.
            start_heat_algorithm: 'snake' or 'random'.
            start_heat_jump_length: Step size between points.

        Returns:
            List of (x, y) tuples.

        Raises:
            ValueError: If algorithm is not 'snake' or 'random'.
        """
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
        """
        Create a grid of points inside the circle with the specified spacing.

        Args:
            radius: Circle radius.
            jump_length: Grid step size.

        Returns:
            List of (x, y) tuples inside the circle.
        """
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
        """
        Randomly shuffle the point order.

        Args:
            points: List of (x, y) tuples.

        Returns:
            New list with same points in random order.
        """
        # Make a copy to avoid modifying the original
        shuffled_points = points.copy()
        random.shuffle(shuffled_points)
        return shuffled_points
    
    
    def _order_points_single_directional(self,points, start_direction_degrees):
        """
        Order points along a single scan direction (lines perpendicular to that direction).

        Args:
            points: List of (x, y) tuples.
            start_direction_degrees: Scan direction angle in degrees (0 = right, 90 = up).

        Returns:
            List of (x, y) tuples in scan order.
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
        Order points in a snake (zigzag) pattern along the scan direction.

        Args:
            points: List of (x, y) tuples.
            start_direction_degrees: Scan direction angle in degrees.

        Returns:
            List of (x, y) tuples in snake order.
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
        Generate points for the jump-safe (pre-heat) pattern in a circular region.

        Uses the same strategies as start heat: random, single directional, or snake.

        Args:
            start_heat_shape: Shape (e.g. circle).
            start_heat_dimension: Radius.
            start_heat_algorithm: 'random', 'single directional', or 'snake'.
            start_heat_jump_length: Step between points.
            start_direction: Direction angle in degrees for directional/snake.

        Returns:
            List of (x, y) coordinates in the chosen order.
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
        Generate points for the postcooling (heat balance) pattern in a circular region.

        Uses the same strategies as start heat: random, single directional, or snake.

        Args:
            start_heat_shape: Shape (e.g. circle).
            start_heat_dimension: Radius.
            start_heat_algorithm: 'random', 'single directional', or 'snake'.
            start_heat_jump_length: Step between points.
            start_direction: Direction angle in degrees for directional/snake.

        Returns:
            List of (x, y) coordinates in the chosen order.
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
            
            

