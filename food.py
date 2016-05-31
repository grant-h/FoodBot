import re

EMOJI_FOOD = [
"chicken",
"turkey",
"fish",
"cow2[beef|cow]",
"crab",
"cheese_wedge[cheese]",
"pig2[bacon|pig]",
"seedling[bean|beans|green|pea|peas|vegetable|vegetables]",
"mushroom[mushrooms]",

"coffee",
"tea",
"beer[alcohol]",
"pizza",
"hamburger[hamburgers]",
"fries",
"poultry_leg",
"meat_on_bone[meat]",
"spaghetti[pasta]",
"curry",
"fried_shrimp[shrimp]",
"bento",
"sushi",
"rice",
"ramen[noodles]",
"stew[soup]",
"oden",
"dango",
"egg[eggs]",
"bread",
"doughnut",
"custard",
"icecream",
"ice_cream",
"shaved_ice",
"birthday",
"cake[cupcake|cupcakes]",
"cookie[cookies]",
"chocolate_bar[chocolate|brownie|brownies]",
"candy",
"lollipop",
"honey_pot",
"apple",
"green_apple",
"tangerine",
"lemon",
"cherries[cherry]",
"grapes",
"watermelon",
"strawberry[strawberries]",
"peach",
"melon",
"banana",
"pear",
"pineapple",
"sweet_potato[potatoes|potato]",
"eggplant",
"tomato",
"corn"
]

EMOJI_DICT = {}

for emoji_spec in EMOJI_FOOD:
    match = re.match(r"([a-z0-9_]+)(\[[a-z0-9_| ]+\])?", emoji_spec)

    key = match.group(1)

    assert key is not None

    EMOJI_DICT.update({key : ":{}:".format(key)})

    if match.group(2):
        alternates = match.group(2)
        alternates = alternates.strip("[]").split("|")

        for alt in alternates:
            alt = alt.strip()
            assert alt not in EMOJI_DICT
            EMOJI_DICT.update({alt : ":{}:".format(key)})
