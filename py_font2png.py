# Source by github.com/zeittresor
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import os, time, random, shutil, math
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps, ImageFilter, ImageChops, ImageMath

class ToolTip:
    def __init__(self, widget, text="info"):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
    def enter(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, background="#ffffff",
                         relief="solid", borderwidth=1, font=("tahoma", 8))
        label.pack(ipadx=1)
    def leave(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

root = tk.Tk()
root.title("font2png")

font_path = None
fonts_folder = os.path.join(os.path.dirname(__file__), "fonts")

var_outline = tk.BooleanVar()
var_rainbow = tk.BooleanVar()
var_noise   = tk.BooleanVar()
var_cloud   = tk.BooleanVar()
var_colorfill = tk.BooleanVar()
var_fractal = tk.BooleanVar()
var_transparent = tk.BooleanVar()

var_outline.set(False)
var_rainbow.set(False)
var_noise.set(False)
var_cloud.set(False)
var_colorfill.set(True)
var_fractal.set(False)
var_transparent.set(True)

color_outline = (255, 0, 0)
color_fill    = (255, 255, 255)
color_cloud   = (255, 255, 255)

rainbow_scale_var   = tk.DoubleVar(value=1.0)
noise_alpha_var     = tk.DoubleVar(value=0.5)
noise_intensity_var = tk.DoubleVar(value=1.0)
cloud_alpha_var     = tk.DoubleVar(value=0.5)
outline_thick_var   = tk.IntVar(value=3)
color_alpha_var     = tk.DoubleVar(value=1.0)
fractal_alpha_var   = tk.DoubleVar(value=1.0)
fractal_zoom_var    = tk.DoubleVar(value=1.0)

def copy_system_fonts():
    source_dir = r"C:\Windows\Fonts"
    if not os.path.exists(source_dir):
        messagebox.showerror("Error", "Cannot find C:\\Windows\\Fonts directory.")
        return
    if not os.path.exists(fonts_folder):
        os.makedirs(fonts_folder)
    try:
        count_copied = 0
        for file in os.listdir(source_dir):
            if file.lower().endswith(".ttf"):
                src = os.path.join(source_dir, file)
                dst = os.path.join(fonts_folder, file)
                if not os.path.exists(dst):
                    shutil.copyfile(src, dst)
                    count_copied += 1
        messagebox.showinfo("Info", f"Copied {count_copied} .ttf files to 'fonts' folder.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not copy fonts.\n{e}")

def choose_font():
    global font_path
    initial_dir = fonts_folder if os.path.exists(fonts_folder) else os.getcwd()
    file_path = filedialog.askopenfilename(
        title="Select font file",
        initialdir=initial_dir,
        filetypes=[("TrueType Font", "*.ttf"), ("All Files", "*.*")]
    )
    if file_path:
        font_path = file_path
        btn_font.config(text=os.path.basename(file_path))

def sanitize_char_for_filename(c):
    special_map = {
        '$': "dollar", '%': "percent", '&': "ampersand", '@': "at",
        '#': "hash", '*': "asterisk", '+': "plus", '?': "question",
        '!': "exclamation", '/': "slash", '\\': "backslash",
        ':': "colon", '|': "pipe", '"': "quote", '<': "lt", '>': "gt"
    }
    if c.isupper():
        return f"Large_[{c}]"
    elif c.islower():
        return f"Small_[{c}]"
    elif c in special_map:
        return special_map[c]
    else:
        return f"char_{ord(c)}"

def measure_text_bbox(font, text):
    tmp_img = Image.new("L", (2000,2000), 0)
    d = ImageDraw.Draw(tmp_img)
    d.text((0,0), text, fill=255, font=font)
    bbox = tmp_img.getbbox()
    if not bbox:
        return (0, 0, 0, 0)
    return bbox

def generate_rainbow(width, height):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    colors = [(255,0,0),(255,127,0),(255,255,0),(0,255,0),(0,0,255),(75,0,130),(148,0,211)]
    for y in range(height):
        c_index = int(y/(height/len(colors)))
        if c_index >= len(colors) - 1:
            c_index = len(colors) - 2
        ratio = (y - (c_index*height/len(colors))) / (height/len(colors))
        r = int(colors[c_index][0]*(1-ratio) + colors[c_index+1][0]*ratio)
        g = int(colors[c_index][1]*(1-ratio) + colors[c_index+1][1]*ratio)
        b = int(colors[c_index][2]*(1-ratio) + colors[c_index+1][2]*ratio)
        d.line([(0,y),(width,y)], fill=(r,g,b))
    return img

def generate_noise(width, height, intensity=1.0):
    img = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(img)
    for y in range(height):
        for x in range(width):
            val = int(random.random() * 255 * intensity)
            d.point((x,y), fill=val)
    return ImageOps.grayscale(img).convert("RGB")

def generate_cloud(width, height, octaves=4):
    base = Image.new("L", (width, height), 0)
    for o in range(octaves):
        layer = Image.new("L", (width, height), 128)
        d = ImageDraw.Draw(layer)
        for y in range(height):
            for x in range(width):
                val = int((random.random() - 0.5) * 255)
                d.point((x,y), fill=val+128)
        layer = layer.filter(ImageFilter.GaussianBlur(8))
        base = ImageChops.add_modulo(base, layer)
    return base.convert("RGB")

def generate_fractal(width, height, zoom=1.0, max_iter=100):
    img = Image.new("RGB", (width, height), "black")
    xmin, xmax = -2.0, 1.0
    ymin, ymax = -1.2, 1.2
    diffx = (xmax - xmin)/(zoom+0.001)
    diffy = (ymax - ymin)/(zoom+0.001)
    cx = -0.5
    cy = 0.0
    scale_x = diffx / width
    scale_y = diffy / height
    for py in range(height):
        y0 = ymin + py * scale_y + cy
        for px in range(width):
            x0 = xmin + px * scale_x + cx
            x, y = 0.0, 0.0
            iteration = 0
            while x*x + y*y <= 4 and iteration < max_iter:
                xtemp = x*x - y*y + x0
                y = 2*x*y + y0
                x = xtemp
                iteration += 1
            c = 255 - int(iteration * 255 / max_iter)
            img.putpixel((px, py), (c, c, 255))
    return img

def blend_images(base_img, overlay_img, alpha):
    return ImageChops.blend(base_img, overlay_img, alpha)

def pick_outline_color():
    global color_outline
    c = colorchooser.askcolor(initialcolor="#FF0000", title="Select Outline Color")
    if c and c[1]:
        color_outline = tuple(int(c[1][i:i+2],16) for i in (1,3,5))
        btn_outline_color.config(text=f"Pick Outline Color\n({c[1]})")

def pick_fill_color():
    global color_fill
    c = colorchooser.askcolor(initialcolor="#FFFFFF", title="Select fill color")
    if c and c[1]:
        color_fill = tuple(int(c[1][i:i+2],16) for i in (1,3,5))
        chk_colorfill.config(text=f"Color Fill ({c[1]})")

def pick_cloud_color():
    global color_cloud
    c = colorchooser.askcolor(initialcolor="#FFFFFF", title="Select cloud color")
    if c and c[1]:
        color_cloud = tuple(int(c[1][i:i+2],16) for i in (1,3,5))
        chk_cloud.config(text=f"Cloud ({c[1]})")

def generate_images():
    global font_path
    text_input = entry_text.get()
    if not font_path:
        messagebox.showerror("Error", "Select a font file first.")
        return
    if not text_input.strip():
        messagebox.showerror("Error", "Enter text first.")
        return
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    square_size = screen_h
    output_dir = os.path.join(os.path.dirname(__file__), "images")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for char in text_input:
        top = tk.Toplevel(root)
        top.attributes('-fullscreen', True)
        top.configure(bg="black")
        font_size = square_size
        chosen_font = None
        while font_size > 0:
            test_font = ImageFont.truetype(font_path, font_size)
            bb = measure_text_bbox(test_font, char)
            w = bb[2] - bb[0]
            h = bb[3] - bb[1]
            if w <= square_size and h <= square_size:
                chosen_font = test_font
                break
            font_size -= 1
        if not chosen_font:
            chosen_font = ImageFont.truetype(font_path, 10)
        if var_transparent.get():
            letter_img = Image.new("RGBA", (square_size, square_size), (0,0,0,0))
            effect_base = Image.new("RGBA", (square_size, square_size), (0,0,0,0))
        else:
            letter_img = Image.new("RGBA", (square_size, square_size), (0,0,0,255))
            effect_base = Image.new("RGBA", (square_size, square_size), (0,0,0,255))
        mask_img = Image.new("L", (square_size, square_size), 0)
        bb = measure_text_bbox(chosen_font, char)
        w = bb[2] - bb[0]
        h = bb[3] - bb[1]
        x_pos = (square_size - w) // 2
        y_pos = (square_size - h) // 2
        draw_mask = ImageDraw.Draw(mask_img)
        draw_mask.text((x_pos - bb[0], y_pos - bb[1]), char, fill=255, font=chosen_font)
        if var_rainbow.get():
            rb = generate_rainbow(square_size, square_size).convert("RGBA")
            effect_base = blend_images(effect_base, rb, rainbow_scale_var.get())
        if var_noise.get():
            nimg = generate_noise(square_size, square_size, intensity=noise_intensity_var.get()).convert("RGBA")
            effect_base = blend_images(effect_base, nimg, noise_alpha_var.get())
        if var_cloud.get():
            cbase = generate_cloud(square_size, square_size, octaves=4).convert("L")
            cbase = ImageOps.colorize(cbase, black="#000000", white="#{:02x}{:02x}{:02x}".format(*color_cloud)).convert("RGBA")
            effect_base = blend_images(effect_base, cbase, cloud_alpha_var.get())
        if var_fractal.get():
            fract = generate_fractal(square_size, square_size, zoom=fractal_zoom_var.get(), max_iter=100).convert("RGBA")
            effect_base = blend_images(effect_base, fract, fractal_alpha_var.get())
        if var_colorfill.get():
            fill_img = Image.new("RGBA", (square_size, square_size), color_fill + (255,))
            effect_base = blend_images(effect_base, fill_img, color_alpha_var.get())
        letter_layer = Image.composite(effect_base, letter_img, mask_img)
        if var_outline.get():
            size_val = outline_thick_var.get()
            if size_val < 3:
                size_val = 3
            if size_val % 2 == 0:
                size_val += 1
            expanded_mask = mask_img.filter(ImageFilter.MaxFilter(size_val))
            ring = ImageMath.eval("convert(a - b, 'L')", a=expanded_mask, b=mask_img)
            outline_layer = Image.new("RGBA", (square_size, square_size), color_outline + (255,))
            letter_img = Image.composite(outline_layer, letter_img, ring)
        letter_img = Image.composite(letter_layer, letter_img, mask_img)
        display_img = Image.new("RGBA", (screen_w, screen_h), (0,0,0,255))
        disp_x = (screen_w - square_size) // 2
        disp_y = (screen_h - square_size) // 2
        display_img.paste(letter_img, (disp_x, disp_y), letter_img)
        tk_image = ImageTk.PhotoImage(display_img.convert("RGB"))
        label = tk.Label(top, image=tk_image, bg="black")
        label.pack(fill="both", expand=True)
        top.update()
        time.sleep(0.5)
        filename = f"{sanitize_char_for_filename(char)}.png"
        if var_transparent.get():
            letter_img.save(os.path.join(output_dir, filename))
        else:
            letter_img.convert("RGB").save(os.path.join(output_dir, filename))
        top.destroy()
    messagebox.showinfo("Done", "All images saved in 'images' folder.")

btn_copyfonts = tk.Button(root, text="Copy System Fonts", command=copy_system_fonts)
btn_copyfonts.pack(pady=5)
ToolTip(btn_copyfonts, "Tries to copy all .ttf from C:\\Windows\\Fonts to a local 'fonts' folder")

btn_font = tk.Button(root, text="Select Font", command=choose_font)
btn_font.pack(pady=5)
ToolTip(btn_font, "Choose a TTF font file (defaults to local 'fonts' folder if available)")

entry_text = tk.Entry(root, width=60)
entry_text.insert(0, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÖÄÜöäü1234567890+-*/!?%$&")
entry_text.pack(pady=5)
ToolTip(entry_text, "Enter the characters you want to convert")

frm_effects = tk.Frame(root)
frm_effects.pack()

chk_transparent = tk.Checkbutton(frm_effects, text="Transparent Background", variable=var_transparent)
chk_transparent.grid(row=0, column=0, sticky="w")
ToolTip(chk_transparent, "Save final PNGs with transparent background")

chk_outline = tk.Checkbutton(frm_effects, text="Outline", variable=var_outline, anchor="w")
chk_outline.grid(row=1, column=0, sticky="w")
ToolTip(chk_outline, "Draw an outline around the character")

outline_slider = tk.Scale(frm_effects, from_=1, to=15, orient="horizontal", variable=outline_thick_var)
outline_slider.grid(row=1, column=1, sticky="w")
ToolTip(outline_slider, "Outline thickness")

btn_outline_color = tk.Button(frm_effects, text="Pick Outline Color", command=pick_outline_color)
btn_outline_color.grid(row=1, column=2, padx=10)
ToolTip(btn_outline_color, "Choose Outline Color")

chk_rainbow = tk.Checkbutton(frm_effects, text="Rainbow", variable=var_rainbow, anchor="w")
chk_rainbow.grid(row=2, column=0, sticky="w")
ToolTip(chk_rainbow, "Fill the character with a rainbow gradient")

rainbow_scale = tk.Scale(frm_effects, from_=0.0, to=1.0, orient="horizontal", resolution=0.1, variable=rainbow_scale_var)
rainbow_scale.grid(row=2, column=1, sticky="w")
ToolTip(rainbow_scale, "Rainbow intensity")

chk_noise = tk.Checkbutton(frm_effects, text="Noise", variable=var_noise, anchor="w")
chk_noise.grid(row=3, column=0, sticky="w")
ToolTip(chk_noise, "Add a random noise effect")

noise_alpha_scale = tk.Scale(frm_effects, from_=0.0, to=1.0, orient="horizontal", resolution=0.1, variable=noise_alpha_var)
noise_alpha_scale.grid(row=3, column=1, sticky="w")
ToolTip(noise_alpha_scale, "Noise alpha-blend")

noise_intensity_scale = tk.Scale(frm_effects, from_=0.1, to=2.0, orient="horizontal", resolution=0.1, variable=noise_intensity_var)
noise_intensity_scale.grid(row=3, column=2, sticky="w")
ToolTip(noise_intensity_scale, "Noise intensity (grain)")

chk_cloud = tk.Checkbutton(frm_effects, text="Cloud", variable=var_cloud, anchor="w")
chk_cloud.grid(row=4, column=0, sticky="w")
ToolTip(chk_cloud, "Add a cloud-like effect")

cloud_alpha_scale = tk.Scale(frm_effects, from_=0.0, to=1.0, orient="horizontal", resolution=0.1, variable=cloud_alpha_var)
cloud_alpha_scale.grid(row=4, column=1, sticky="w")
ToolTip(cloud_alpha_scale, "Cloud alpha-blend")

btn_cloud_color = tk.Button(frm_effects, text="Pick Cloud Color", command=pick_cloud_color)
btn_cloud_color.grid(row=4, column=2, padx=10)
ToolTip(btn_cloud_color, "Choose the base color for the Cloud effect")

chk_fractal = tk.Checkbutton(frm_effects, text="Fractal Fill", variable=var_fractal, anchor="w")
chk_fractal.grid(row=5, column=0, sticky="w")
ToolTip(chk_fractal, "Fill the character with a Mandelbrot fractal")

fractal_zoom_scale = tk.Scale(frm_effects, from_=0.5, to=5.0, orient="horizontal", resolution=0.5, variable=fractal_zoom_var)
fractal_zoom_scale.grid(row=5, column=1, sticky="w")
ToolTip(fractal_zoom_scale, "Fractal zoom factor")

fractal_alpha_scale = tk.Scale(frm_effects, from_=0.0, to=1.0, orient="horizontal", resolution=0.1, variable=fractal_alpha_var)
fractal_alpha_scale.grid(row=5, column=2, sticky="w")
ToolTip(fractal_alpha_scale, "Fractal alpha-blend")

chk_colorfill = tk.Checkbutton(frm_effects, text="Color Fill", variable=var_colorfill, anchor="w")
chk_colorfill.grid(row=6, column=0, sticky="w")
ToolTip(chk_colorfill, "Fill the character with a single color")

color_scale = tk.Scale(frm_effects, from_=0.0, to=1.0, orient="horizontal", resolution=0.1, variable=color_alpha_var)
color_scale.grid(row=6, column=1, sticky="w")
ToolTip(color_scale, "Color fill alpha-blend")

btn_fill_color = tk.Button(frm_effects, text="Pick Fill Color", command=pick_fill_color)
btn_fill_color.grid(row=6, column=2, padx=10)
ToolTip(btn_fill_color, "Choose the fill color if Color Fill is checked")

btn_generate = tk.Button(root, text="Generate", command=generate_images)
btn_generate.pack(pady=10)
ToolTip(btn_generate, "Generate PNG images for each character in full screen")

root.mainloop()
