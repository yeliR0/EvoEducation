import math
import random
import pygame
import sys

#MAYBE ADD NUTRIENTS LATER
#MAYBE ADD TEMPERATURE LATER
#MAYBE ADD MEMBRANE SATURATEDNESS LATER

simSpeed = 1 #Speed of simulation
numCells = 20 #BASE NUMBER
foodFertility = 0.004 #BASE NUMBER; food created per timestep
friction = 0.7
angleFriction = 0.6
sizeFactor = 25
fullnessFactor = 0.6 #how much energy you get from food (less is less energy)
reproductionThreshold = 0.85
reproductionCost = 0.5
deathWasteFactor = 0.7 #how much of  size turns into food when death
baseEnergyCost = 0.00002 #energy cost per timestep
speedEnergyCost = 0.001 #energy cost multiplier for acceleration
wanderingSpeed = 0.005 #speed increase when nothing is seen
foodSightSpeed = 0.01 #speed increase when food is seen
turnStrength = 0.05  # smaller = smoother turning
eatingFactor = 0.5 #how fast you can eat
healCost = 0.00005 #energy cost multiplier for healing
healness = 0.0001 #how fast you heal
healEnergyThreshold = 0.4 #minimum energy to heal
metabolismRate = 0.005 #how fast convert stored food to energy
sightDistance = 150

selectedItem = None
cells = []
deadCells = []
food = []
cellid = 0
foodid = 0
pause = False


# Initialize pygame
pygame.init()

# Set up the window
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MultiCell")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
font = pygame.font.SysFont(None, 28)
bigfont = pygame.font.SysFont(None, 72)
clock = pygame.time.Clock()

class Cell:
    def __init__(self, id, x, y, direction, speed, dangle, size, health, fov, energy, foodStored, wallpermeability, internalSA, goTowardsOther):
        self.id = id
        self.x = x
        self.y = y
        self.direction = direction  # in degrees
        self.speed = speed  # units per time step 
        self.dangle = dangle # degrees per time step
        self.fov = fov  # field of view in degrees
        self.size = size  # area 0-1
        self.health = health  # 0-1
        self.radius = math.sqrt(size/math.pi)*sizeFactor
        self.energy = energy  # hunger
        self.foodStored = foodStored  # food stored internally (0-1)
        self.wallpermeability = wallpermeability  # ability to be penetrated (0-1)
        self.internalSA = internalSA  # internal surface area (0-1)
        self.goTowardsOther = goTowardsOther  # whether to move towards other cells

    def see(self, cell_tree, food_tree):
        search_area = pygame.Rect(
            self.x - sightDistance,
            self.y - sightDistance,
            sightDistance * 2,
            sightDistance * 2
        )
        nearby_food = food_tree.query(search_area, [])
        nearby_cells = cell_tree.query(search_area, [])
        closestFood = None
        closerCell = None

        # Check nearby food
        for fooditem in nearby_food:
            angle_to_food = math.degrees(math.atan2(fooditem.y - self.y, fooditem.x - self.x)) % 360
            angle_diff = (angle_to_food - self.direction + 180) % 360 - 180
            distance = math.hypot(fooditem.x - self.x, fooditem.y - self.y)
            if abs(angle_diff) <= self.fov / 2 and distance <= sightDistance:
                if closestFood is None or distance < closestFood[0]:
                    closestFood = (distance, angle_diff)

        # Check nearby cells
        if self.goTowardsOther:
            for cell in nearby_cells:
                if cell != self:
                    angle_to_cell = math.degrees(math.atan2(cell.y - self.y, cell.x - self.x)) % 360
                    angle_diff = (angle_to_cell - self.direction + 180) % 360 - 180
                    distance = math.hypot(cell.x - self.x, cell.y - self.y)
                    if abs(angle_diff) <= self.fov / 2 and distance <= sightDistance:
                        if closestFood is None or distance < closestFood[0]:
                            closerCell = (distance, angle_diff)
        
        if closerCell:
            _, angle_diff = closerCell
            self.speed += foodSightSpeed
            self.dangle = min(1,angle_diff * turnStrength)
        elif closestFood:
            _, angle_diff = closestFood
            self.speed += foodSightSpeed
            self.dangle = min(1,angle_diff * turnStrength)
        else:
            self.speed += wanderingSpeed
        
    def eat(self, fooditem):
        #check if fooditem is food
        if fooditem in food:
            fooditem.size -= min(fooditem.size, min(1-self.foodStored, self.wallpermeability * self.size * eatingFactor))
            self.speed -= 7*self.radius/sizeFactor
            self.foodStored += fullnessFactor * min(fooditem.size, self.wallpermeability * self.size * eatingFactor)
            self.foodStored = min(self.internalSA*self.size, self.foodStored) #internal surface area limits food storage
            if fooditem.size <= 0:
                food.remove(fooditem)
        #check if fooditem is another cell
        elif fooditem in cells and fooditem != self:
            fooditem.health -= min(fooditem.health, fooditem.wallpermeability * self.size * eatingFactor)
            self.speed -= 7*self.radius/sizeFactor
            if fooditem.health <= 0:
                fooditem.die()
    
    def metabolize(self):
        if self.energy < 1 and self.foodStored > 0:
            self.energy += metabolismRate * self.internalSA * self.foodStored
            self.foodStored -= metabolismRate * self.internalSA * self.foodStored
            self.energy = min(1, self.energy)
            self.foodStored = max(0, self.foodStored)

    def reproduce(self):
        if self.energy >= reproductionThreshold and self.health >= 0.8:
            self.energy -= self.size * reproductionCost
            spawnAngle = random.uniform(0, 360)
            spawnDistance = self.radius * (1 + random.uniform(0, 1))
            if wallPermeabilityToggle == True:
                wallpermeability = min(1,max(0,self.wallpermeability + random.uniform(-0.1, 0.1)))
            else:
                wallpermeability = 0.5
            if internalSAToggle == True:
                internalSA = min(1,max(0,self.internalSA + random.uniform(-0.1, 0.1)))
            else:
                internalSA = 0.5
            if goTowardsOthersToggle == True:
                if random.choices([True, False], weights=[0.10,0.90])[0] == True:
                    goTowardsOther = random.choices([True, False])[0]
                else:
                    goTowardsOther = self.goTowardsOther
            else:
                goTowardsOther = False
            create_cell(self.x+math.cos(spawnAngle*math.pi/180)*spawnDistance, self.y+math.sin(spawnAngle*math.pi/180)*spawnDistance, random.uniform(0, 360), min(1,max(0.05,self.size + random.uniform(-0.05, 0.05))), wallpermeability, internalSA, goTowardsOther)
    
    def heal(self):
        if self.health < 1 and self.energy > healEnergyThreshold:
            self.health += healness
            self.energy -= healCost * self.size
            self.health = min(1, self.health)

    def die(self):
        if self not in deadCells:  # prevent double removal
            deadCells.append(self)
            create_food(self.x, self.y, size = deathWasteFactor * self.size)
class Food:
    def __init__(self, id, x, y, size):
        self.id = id
        self.x = x
        self.y = y
        self.size = size  # area
        self.radius = math.sqrt(size/math.pi)*sizeFactor

def create_cell(x, y, direction, size, wallpermeability, internalSA, goTowardsOther):
    global cellid
    id = cellid
    cellid += 1
    speed, dangle, foodStored = 0, 0, 0
    fov = 140
    health = 1
    energy = 0.7
    cell = Cell(id, x, y, direction, speed, dangle, size, health, fov, energy, foodStored, wallpermeability, internalSA, goTowardsOther)
    cells.append(cell)

def create_food(x, y, size):
    global foodid
    id = foodid
    foodid += 1
    fooditem = Food(id, x, y, size)
    food.append(fooditem)

def showStartScreen():
    screen.fill(WHITE)
    title = bigfont.render("EvoEducation", True, BLACK)
    subtitle = font.render("Press SPACE to begin", True, BLACK)
    credit = font.render("by Riley Lambert", True, (80, 80, 80))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, HEIGHT // 2))
    screen.blit(credit, (WIDTH - credit.get_width() - 10, HEIGHT - 40))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
        clock.tick(60)

    showSettingsScreen()

def showSettingsScreen():
    #UI for settings created by ChatGPT
    global numCells, foodFertility, wallPermeabilityToggle, internalSAToggle, goTowardsOthersToggle

    # Default values
    numCells = 20
    foodFertilityPercent = 50
    wallPermeabilityToggle = True
    internalSAToggle = True
    goTowardsOthersToggle = True

    # --- Slider setup ---
    sliders = [
        {"label": "Initial # of Cells", "min": 1, "max": 200, "value": numCells, "y": 160},
        {"label": "Food Fertility (%)", "min": 0, "max": 100, "value": foodFertilityPercent, "y": 240},
    ]
    slider_x = 250
    slider_width = 300
    slider_height = 6
    knob_radius = 10
    dragging = None  # which slider index is being dragged

    # --- Checkbox setup ---
    checkbox_y_start = 320
    checkbox_spacing = 40
    checkboxes = [
        {"label": "Wall Permeability", "value": wallPermeabilityToggle},
        {"label": "Internal Surface Area", "value": internalSAToggle},
        {"label": "Cell Targeting", "value": goTowardsOthersToggle},
    ]
    checkbox_rects = []

    def draw_slider(label, value, minv, maxv, y):
        pygame.draw.rect(screen, (180, 180, 180), (slider_x, y, slider_width, slider_height))
        normalized = (value - minv) / (maxv - minv)
        knob_x = slider_x + normalized * slider_width
        pygame.draw.circle(screen, (100, 100, 255), (int(knob_x), y + slider_height // 2), knob_radius)
        label_text = font.render(f"{label}:", True, BLACK)
        value_text = font.render(str(int(value)), True, BLACK)
        screen.blit(label_text, (30, y - 10))
        screen.blit(value_text, (slider_x + slider_width + 40, y - 10))
        return knob_x, y + slider_height // 2

    def draw_checkbox(x, y, label, checked):
        size = 20
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, BLACK, rect, 2)
        if checked:
            pygame.draw.line(screen, BLACK, (x + 3, y + 10), (x + 8, y + 15), 3)
            pygame.draw.line(screen, BLACK, (x + 8, y + 15), (x + 17, y + 5), 3)
        label_text = font.render(label, True, BLACK)
        screen.blit(label_text, (x + 30, y))
        return rect

    def draw_all():
        screen.fill(WHITE)
        title = bigfont.render("Parameters", True, BLACK)
        instruction = font.render("Press SPACE to start simulation", True, BLACK)
        screen.blit(title, (30, 10))
        screen.blit(instruction, (330, 30))

        knob_positions = []
        for s in sliders:
            knob_positions.append(
                draw_slider(s["label"], s["value"], s["min"], s["max"], s["y"])
            )

        # Draw checkboxes
        checkbox_rects.clear()
        for i, c in enumerate(checkboxes):
            rect = draw_checkbox(30, checkbox_y_start + i * checkbox_spacing, c["label"], c["value"])
            checkbox_rects.append(rect)

        pygame.display.flip()
        return knob_positions

    knob_positions = draw_all()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Check sliders
                for i, s in enumerate(sliders):
                    knob_x, knob_y = knob_positions[i]
                    if abs(mx - knob_x) < 15 and abs(my - knob_y) < 15:
                        dragging = i
                        break
                # Check checkboxes
                for i, rect in enumerate(checkbox_rects):
                    if rect.collidepoint(mx, my):
                        checkboxes[i]["value"] = not checkboxes[i]["value"]

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = None

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False

        if dragging is not None:
            mx, my = pygame.mouse.get_pos()
            s = sliders[dragging]
            mx = max(slider_x, min(mx, slider_x + slider_width))
            normalized = (mx - slider_x) / slider_width
            s["value"] = s["min"] + normalized * (s["max"] - s["min"])

        knob_positions = draw_all()
        clock.tick(60)

    # Export values
    numCells = int(sliders[0]["value"])
    foodFertility = (0.004*2/100)*sliders[1]["value"]
    wallPermeabilityToggle = checkboxes[0]["value"]
    internalSAToggle = checkboxes[1]["value"]
    goTowardsOthersToggle = checkboxes[2]["value"]

# Start screen
showStartScreen()

for _ in range(numCells):
    x = random.uniform(0, WIDTH)
    y = random.uniform(0, HEIGHT)
    size = random.uniform(0.01, 1)
    if wallPermeabilityToggle == True:
        wallpermeability = random.uniform(0, 1)
    else:
        wallpermeability = 0.5
    if internalSAToggle == True:
        internalSA = random.uniform(0, 1)
    else:
        internalSA = 0.5
    if goTowardsOthersToggle == True:
        goTowardsOther = random.choices([True, False])[0]
    else:
        goTowardsOther = False
    create_cell(x, y, random.uniform(0, 360), size, wallpermeability, internalSA, goTowardsOther)

# ==============================
# QUADTREE IMPLEMENTATION
# ==============================
class Quadtree:
    def __init__(self, boundary, capacity=5):
        self.boundary = boundary  # pygame.Rect
        self.capacity = capacity
        self.points = []
        self.divided = False

    def subdivide(self):
        x, y, w, h = self.boundary
        hw, hh = w / 2, h / 2
        self.nw = Quadtree(pygame.Rect(x, y, hw, hh), self.capacity)
        self.ne = Quadtree(pygame.Rect(x + hw, y, hw, hh), self.capacity)
        self.sw = Quadtree(pygame.Rect(x, y + hh, hw, hh), self.capacity)
        self.se = Quadtree(pygame.Rect(x + hw, y + hh, hw, hh), self.capacity)
        self.divided = True

    def insert(self, obj):
        if not self.boundary.collidepoint(obj.x, obj.y):
            return False

        if len(self.points) < self.capacity:
            self.points.append(obj)
            return True
        else:
            if not self.divided:
                self.subdivide()
            return (
                self.nw.insert(obj) or self.ne.insert(obj) or
                self.sw.insert(obj) or self.se.insert(obj)
            )

    def query(self, range_rect, found):
        if not self.boundary.colliderect(range_rect):
            return
        for p in self.points:
            if range_rect.collidepoint(p.x, p.y):
                found.append(p)
        if self.divided:
            self.nw.query(range_rect, found)
            self.ne.query(range_rect, found)
            self.sw.query(range_rect, found)
            self.se.query(range_rect, found)
        return found

def timestep():
    # Build quadtrees for spatial lookup
    boundary = pygame.Rect(0, 0, WIDTH, HEIGHT)
    cell_tree = Quadtree(boundary)
    food_tree = Quadtree(boundary)
    for c in cells:
        cell_tree.insert(c)
    for f in food:
        food_tree.insert(f)

    for cell in cells[:]:
        # Update position
        rad = math.radians(cell.direction)
        cell.x += cell.speed * math.cos(rad)
        cell.y += cell.speed * math.sin(rad)
        cell.direction = (cell.direction + cell.dangle) % 360
        cell.dangle *= friction
        cell.speed *= angleFriction

        # Wrap-around
        cell.x %= WIDTH
        cell.y %= HEIGHT

        # Energy consumption
        cell.metabolize()
        cell.energy -= baseEnergyCost * cell.size
        cell.energy -= cell.speed * speedEnergyCost * cell.size

        # Check death
        if cell.energy <= 0 or cell.health <= 0:
            cell.die()
            continue

        search_radius = cell.radius * 2
        search_area = pygame.Rect(
            cell.x - search_radius,
            cell.y - search_radius,
            search_radius * 2,
            search_radius * 2,
        )

        # Nearby food
        nearby_food = food_tree.query(search_area, [])
        for f in nearby_food:
            distance = math.hypot(f.x - cell.x, f.y - cell.y)
            if distance < cell.radius + f.radius:
                cell.eat(f)
                break

        # Nearby cells
        nearby_cells = cell_tree.query(search_area, [])
        for other in nearby_cells:
            if other is not cell:
                distance = math.hypot(other.x - cell.x, other.y - cell.y)
                if distance < cell.radius + other.radius:
                    cell.eat(other)
                    break

        # Vision, healing, reproduction
        cell.see(cell_tree, food_tree)
        cell.heal()
        cell.reproduce()

    # Food generation
    if random.random() < foodFertility:
        create_food(random.uniform(0, WIDTH), random.uniform(0, HEIGHT), size=random.uniform(0, 1))
    
    for dead in deadCells:
        if dead in cells:
            cells.remove(dead)
    deadCells.clear()

# GUI state
def draw_cell_info(item):
    if item is None:
        return
    if isinstance(item, Cell):  # It's a Cell
        info_lines = [
            f"ID: {item.id}",
            f"Health: {round(item.health*100,2):.2f}%",
            f"Size: {round(item.size*100,2):.2f}%",
            f"Wall Permeability: {round(item.wallpermeability*100,2):.3f}%",
            f"Internal SA: {round(item.internalSA*100,2):.3f}%",
            f"Energy: {round(item.energy*100,2):.2f}%",
            f"Food Stored: {round(item.foodStored/(item.size*item.internalSA)*100,2):.2f}%",
            f"Direction: {item.direction:.1f}°",
            f"Speed: {item.speed:.3f}",
            f"Go Towards Other Cells: {item.goTowardsOther}"
        ]
    else:  # It's Food
        info_lines = [
            f"ID: {item.id}",
            f"Size: {round(item.size*100,2):.2f}%"
        ]
    for i, line in enumerate(info_lines):
        text = font.render(line, True, (0, 0, 0))
        screen.blit(text, (10, 10 + i * 30))

def drawCellFOV (item):     
    # Draw FOV triangle
    # Draw FOV as a filled arc (sector)
    fov_angle = item.fov
    distance = sightDistance
    center = (int(item.x), int(item.y))
    dir_deg = item.direction

    # Calculate points along the arc
    num_points = 30
    start_angle = dir_deg - fov_angle / 2
    end_angle = dir_deg + fov_angle / 2
    arc_points = [center]
    for i in range(num_points + 1):
        angle = math.radians(start_angle + (end_angle - start_angle) * i / num_points)
        x = int(item.x + distance * math.cos(angle))
        y = int(item.y + distance * math.sin(angle))
        arc_points.append((x, y))
    pygame.draw.polygon(
        screen,
        (200, 200, 255, 80),
        arc_points,
        0
    )

# Main sim loop
while pause != True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            clicked = None
            for cell in cells:
                distance = math.hypot(mx - cell.x, my - cell.y)
                if distance <= cell.radius:  # check if click inside cell
                    clicked = cell
                    break
            for fooditem in food:
                distance = math.hypot(mx - fooditem.x, my - fooditem.y)
                if distance <= fooditem.radius:  # check if click inside food
                    clicked = fooditem
                    break
            if clicked:
                selectedItem = clicked
            else:
                selectedItem = None

    screen.fill(WHITE)

    if isinstance(selectedItem, Cell):
        drawCellFOV(selectedItem) 
    else: None

    for _ in range(random.choices([int(simSpeed-simSpeed%1), int(simSpeed-simSpeed%1+1)], weights=[1-(simSpeed%1), simSpeed%1])[0]):
        timestep()

    for cell in cells:
        pygame.draw.circle(screen, (cell.wallpermeability*204, cell.wallpermeability*229, cell.wallpermeability*255), (int(cell.x), int(cell.y)), int(cell.radius))

        # Black outline if selected
        if cell == selectedItem:
            pygame.draw.circle(screen, (0, 0, 0), (int(cell.x), int(cell.y)), int(cell.radius), 2)

        # Marker length (so you can see it clearly)
        marker_length = int(cell.radius * 2)

        # Calculate marker endpoint
        rad = math.radians(cell.direction)
        end_x = cell.x + marker_length * math.cos(rad)
        end_y = cell.y + marker_length * math.sin(rad)

        # Draw the line marker
        pygame.draw.line(screen, (255, 204*cell.internalSA, 204*cell.internalSA), (int(cell.x), int(cell.y)), (int(end_x), int(end_y)), 2)

        # Draw eat others marker
        if cell.goTowardsOther:
            pygame.draw.circle(screen, (255,0,0), (int(cell.x), int(cell.y)), int(cell.radius*0.5), 2)

    for fooditem in food:
        fooditem.radius = math.sqrt(fooditem.size/math.pi)*sizeFactor
        pygame.draw.circle(screen, (0,200,0), (int(fooditem.x), int(fooditem.y)), int(fooditem.radius))

        if fooditem == selectedItem:
            pygame.draw.circle(screen, (0, 0, 0), (int(fooditem.x), int(fooditem.y)), int(fooditem.radius), 2)

    draw_cell_info(selectedItem)
    speed_text = font.render(f"Sim Speed: {simSpeed:.2f}x (Hold arrow keys)", True, (0, 0, 0))
    screen.blit(speed_text, (10, HEIGHT - 30))

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        simSpeed = min(128, simSpeed * 2*(0.5+0.004))
    if keys[pygame.K_DOWN]:
        simSpeed = max(0.01, simSpeed * 0.5*(2-0.03))

    pygame.display.flip()