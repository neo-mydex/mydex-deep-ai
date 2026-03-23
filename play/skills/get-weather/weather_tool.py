
def get_location():
    return "beijing"

def get_weather(city: str):
    d = {"北京":"sunny","深圳":"rainy"}
    return d.get(city, "unknown")