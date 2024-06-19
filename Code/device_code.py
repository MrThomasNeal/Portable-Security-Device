import sensors
import time
import grovelcd
from collections import deque

# Passcode set upon activation
set_passcode = []

# Variables to ensure certain messages are sent only one time within loops
collect_baseline_levels_message = False
begin_monitoring_message = False

# Set the sensor pins
sensor_pins = {"button1":4, "button2":3, "button3":2, "rotary_angle":2, "light":1, "sound":0, "pir":8}
sensors.set_pins(sensor_pins)

# Function to verify the user for activation and deactivation of the device
def verify_user(type_of_event):

    global set_passcode

    # Maximum length the passcode can be set as
    max_passcode_length = 4
    
    # Current length of the inputted passcode
    current_passcode_length = 0
    
    # Store the current passcode
    passcode = []
    
    # Keep the loop going
    run = True

    while run == True:

        # Get the values for each button
        button1_value = sensors.button1.get_level()
        button2_value = sensors.button2.get_level()
        button3_value = sensors.button3.get_level()
    
        # Look for button clicks and add it to the current passcode + track length
        if button1_value == 1:
            passcode.append(1)
            current_passcode_length += 1
        elif button2_value == 1:
            passcode.append(2)
            current_passcode_length += 1
        elif button3_value == 1:
            passcode.append(3)
            current_passcode_length += 1
       
        # If 4 digits have been entered, begin activation and inform the user
        if len(passcode) == 4:
        
            if type_of_event == "Activate":
            
                # Display the passcode on the screen and an activation message
                passcode_string = [str(num) for num in passcode]
                display_passcode = "".join(passcode_string)
                grovelcd.setText("Activated: " + display_passcode)
                print("Activated: " + str(passcode))
                
                # Set the activation passcode as the newly entered passcode
                set_passcode = passcode
                
                # Ask the user to leave the room and escape the iteration
                time.sleep(2)
                grovelcd.setText("Please leave the room!")
                time.sleep(2)
                grovelcd.setRGB(0, 255, 0)
                run = False
                
            elif type_of_event == "Deactivate":
                   
                if passcode == set_passcode:
                
                    # Display the passcode on the screen and a deactivation message
                    passcode_string = [str(num) for num in passcode]
                    display_passcode = "".join(passcode_string)
                    grovelcd.setText("Deactivated: " + display_passcode)
                    print("Deactivated: " + str(passcode))
                    
                    # End the program
                    time.sleep(2)
                    run = False
                    exit()
                    
                else:
                    print("Failed password attempt")
                    run = False
                
        # Show the current passcode on the screen if it hasn't yet been fully entered
        else:
            passcode_string = [str(num) for num in passcode]
            display_passcode = "".join(passcode_string)
            grovelcd.setText(display_passcode)
    
        time.sleep(0.1)

# Function to calculate the probability of an event based on the specified weighting for each sensor
def calculate_probability(light, sound, pir):

    # Turn each sensor value either into a 1/0, from True/False
    light = int(light)
    sound = int(sound)
    pir = int(pir)
    
    # Calculate probability based on specified weighting
    probability = (light * weights["light"]) + (sound * weights["sound"]) + (pir * weights["pir"])
    return probability

# Activate the device then wait 30 seconds for the user to leave the room
verify_user("Activate")
print("Leave room")
time.sleep(30)

# To gather initial readings before detection (ambient level) and track progress
run_count = 0

# Keeps main loop running
deviceActive = True

# History of entries to used determine ambient levels
light_history = deque(maxlen=200)
sound_history = deque(maxlen=200)

# Ambient levels
ambient_light_level = 0
ambient_sound_level = 0

# Initialise sensor trigger variables
light_triggered = False
sound_triggered = False
pir_triggered = False
event_detected = False

# Counter for how long since the last event was triggered
event_detected_counter = 0

# Below are variables to calibrate accuracy

# Thresholding
threshold_trigger = 30

# Probability weights
weights = {"light": 0.3, "sound":0.3, "pir":0.4}

# Threshold that decides whether an event is triggered or not
probability_threshold = 0.4

# Amount of loops until another event can be triggered
event_detected_cooldown = 50

while deviceActive:

    # Clear the LCD screen
    grovelcd.setText("")
    
    # Reset the individual sensor trigger variables
    light_triggered = False
    sound_triggered = False
    pir_triggered = False

    # Implements event notification cooldown so an event can only be triggered every event_detected_cooldown long
    if event_detected_counter > event_detected_cooldown:
        event_detected = False
        event_countdown = 0

    # Get the sensor values from the device for event detection
    light = sensors.light.get_level()
    sound = sensors.sound.get_level()
    pir = sensors.pir.get_level()
    
    # Get the button values from device in case of deactivation
    button1_value = sensors.button1.get_level()
    button2_value = sensors.button2.get_level()
    button3_value = sensors.button3.get_level()
    if button1_value == 1 or button2_value == 1 or button3_value == 1:
        verify_user("Deactivate")

    # Up until 360 iterations, collect data to form the ambient level of the room
    if run_count <= 360: 
    
        # Add the current value to the deques
        light_history.append(light)
        sound_history.append(sound)
        
        # One time message to show user within the terminal that ambient levels are being collected
        if not collect_baseline_levels_message:
            print("Collecting baseline levels...")
            collect_baseline_levels_message = True
        
    # Once ambient levels have been collected and user has left the room, begin detecting events
    if run_count > 360:
    
        # One time message to show user within the terminal that the device is now running and monitoring
        if not begin_monitoring_message:
            print("Now monitoring room...")
            begin_monitoring_message = True
    
        # Calculate the ambient levels of the room
        ambient_light_level = sum(light_history)/len(light_history)
        ambient_sound_level = sum(sound_history)/len(sound_history)

        # Light Sensor: Detect events + add new data to deque
        if light > ambient_light_level + threshold_trigger:
            light_triggered = True
            print(f"Light: Trigger = {light} Ambient = {ambient_light_level}")
        light_history.popleft()
        light_history.append(ambient_light_level)

        # Sound Sensor: Detect events + add new data to deque
        if sound > ambient_sound_level + threshold_trigger:
            sound_triggered = True
            print(f"Sound: Trigger = {sound} Ambient = {ambient_sound_level}")
        sound_history.popleft()
        sound_history.append(ambient_sound_level)
        
        # PIR sensor
        if pir:
            pir_triggered = True
            print("PIR: Triggered")

        # Calculate probability of event
        if light_triggered or sound_triggered or pir_triggered:
            probability = calculate_probability(light_triggered, sound_triggered, pir_triggered)
            print("Calculated probability = " + str(probability))
            if(probability >= probability_threshold):
                if event_detected == False:
                    print(f"EVENT DETECTED (Run Count = {run_count})")
                    event_detected = True
                    event_detected_counter = 0
        else:
            # Set LCD screen colour as green to symbolise "no intrusion"
            grovelcd.setRGB(0, 255, 0)
            event_detected = False

    # Used to implement event notification cooldown + colour LCD screen as red to display detected event
    if event_detected:
        grovelcd.setRGB(255, 0 ,0)
        event_detected_counter += 1
    
    time.sleep(0.05)
    run_count += 1