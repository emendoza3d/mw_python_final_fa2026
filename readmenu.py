from pathlib import Path


def read_menu(file_path=None):
    path = Path(file_path) if file_path is not None else Path(__file__).with_name("menu.txt")
    menus = {}
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            category, separator, detail = line.partition(":")
            if not separator:
                raise ValueError(f"Invalid menu entry on line {line_number}.")
            menus[category.strip().upper()] = detail.strip()
    return menus

def split_into_variables(menu_items):
    shape = menu_items.get("SHAPE")
    style = menu_items.get("STYLE")
    metal = menu_items.get("METAL")
    diamond = menu_items.get("DIAMOND")
    return shape, style, metal, diamond

# def print_menu(shape, style, metal, diamond):
def print_shape(shape):
    print("Shape\n")
    print(shape)
    count = 1
    shape_item = shape.split(',')
    for item in shape_item:
        print(f"{count}.    {item.strip()}")
        count += 1

def print_style(style):
    print("Style\n")
    print(style)
    count = 1
    shape_item = style.split(',')
    for item in shape_item:
        print(f"{count}.    {item.strip()}")
        count += 1

def print_metal(metal):
    print("Metal\n")
    print(metal)
    count = 1
    shape_item = metal.split(',')
    for item in shape_item:
        print(f"{count}.    {item.strip()}")
        count += 1

def print_diamond(diamond):
    print("Diamond\n")
    print(diamond)
    count = 1
    shape_item = diamond.split(',')
    for item in shape_item:
        print(f"{count}.    {item.strip()}")
        count += 1


