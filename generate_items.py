import os

LOCAL_DIR = os.path.dirname(__file__)
CLIP_DIR = os.path.join(LOCAL_DIR, "clips")

template = """<h2>{}</h2>
<div class="item">
    <video autoplay loop muted>
        <source src="clips/{}" type="video/mp4">
    </video>

    <div class="description">
        <div class="desc-box">
            <p>
                Date Created: Unspecified
            </p>
            <p>
                Code: <a href="https://www.google.com">Github</a>
            </p>
        </div>
        <div class="desc-box">
            <p>
                description
            </p>
        </div>
    </div>
</div>
"""

def main():
    include_in_index = []
    for filename in os.listdir(CLIP_DIR):
        title = filename[:-4].replace("-", " ").title()

        html_address = os.path.join(LOCAL_DIR, "items", f"{filename[:-4]}.html")

        with open(html_address, "w") as new_item:
            print(template.format(title, filename), file=new_item)


        include_in_index.append(f"<div data-include=\"{filename[:-4]}\"></div>")

    print("\n".join(include_in_index))

if __name__ == "__main__":
    main()


