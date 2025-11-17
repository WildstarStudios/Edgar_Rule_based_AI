from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom

def create_parrot_tpose_horizontal(filename="parrot_tpose_horizontal.svg"):
    svg = Element('svg', width="250", height="200", xmlns="http://www.w3.org/2000/svg")
    
    # Body
    body = SubElement(svg, 'ellipse', cx="125", cy="120", rx="40", ry="55", fill="#4CAF50")
    
    # Head
    head = SubElement(svg, 'circle', cx="125", cy="70", r="25", fill="#4CAF50")
    
    # Beak
    beak = SubElement(svg, 'polygon', points="125,65 150,75 125,75", fill="#FFC107")
    
    # Eyes
    left_eye = SubElement(svg, 'circle', cx="115", cy="65", r="5", fill="white")
    left_pupil = SubElement(svg, 'circle', cx="115", cy="65", r="2", fill="black")
    
    right_eye = SubElement(svg, 'circle', cx="135", cy="65", r="5", fill="white")
    right_pupil = SubElement(svg, 'circle', cx="135", cy="65", r="2", fill="black")
    
    # Wings (T-pose, fully horizontal, attached to body)
    left_wing = SubElement(svg, 'path', d="M85,120 C50,110 50,140 85,130 Z", fill="#388E3C")  # left wing
    right_wing = SubElement(svg, 'path', d="M165,120 C200,110 200,140 165,130 Z", fill="#388E3C")  # right wing
    
    # Tail
    tail = SubElement(svg, 'polygon', points="110,170 140,170 125,200", fill="#2E7D32")
    
    # Feather accents
    left_feather = SubElement(svg, 'path', d="M80,125 C60,115 60,135 80,130 Z", fill="#2E7D32")
    right_feather = SubElement(svg, 'path', d="M170,125 C190,115 190,135 170,130 Z", fill="#2E7D32")
    
    # Pretty XML
    rough_string = tostring(svg, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_svg = reparsed.toprettyxml(indent="  ")
    
    # Save SVG
    with open(filename, "w") as f:
        f.write(pretty_svg)
    print(f"Parrot T-pose (horizontal wings) SVG saved as {filename}")

# Generate
create_parrot_tpose_horizontal()
