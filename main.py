"""web map"""
import argparse
import folium
from haversine import haversine
from geopy.geocoders import Nominatim, ArcGIS


def read_data(path: str, year: str) -> list:
    """
    Reads data from file. Returns list of tuples 
    where all films were created in the particular year.
    Args:
        path: path to the file
        year: year when films were created
    Returns:
        list: list of tuples(name of film: str, place: str)
    """
    with open(path, encoding='utf-8', errors="ignore") as file:
        info = file.read().strip().split('\n')[14:-1]

    filtered_info = []
    for line in info:
        parts = line.split('\t')
        name_year_line = parts[0]
        additional_info_start = name_year_line.find('{')
        year_start = name_year_line.find('(')
        if additional_info_start != -1 and additional_info_start > year_start:
            name_year_line = name_year_line[:additional_info_start].strip()
        name_year = name_year_line.split(' ')
        if '(' in name_year[-2]:
            del name_year[-1]
        film_year = name_year[-1][1:5]
        if film_year == year:
            if '(' in parts[-1]:
                del parts[-1]
            filtered_info.append([' '.join(name_year[:-1]), parts[-1]])
    return filtered_info


def get_coordinates(place: str) -> tuple:
    """
    Get tuple of latitude and longitude of the place.
    Args:
        place: name of the place
    Returns:
        tuple: tuple with latitude and longitude
    """
    geolocator_1 = Nominatim(user_agent='http')
    geolocator_2 = ArcGIS()
    location = geolocator_1.geocode(place)
    if location is None:
        location = geolocator_2.geocode(place)
    if location is not None:
        return location.latitude, location.longitude
    return


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="creates web map")
    parser.add_argument('film_year', type=str,
                        help='films of which year you want to see')
    parser.add_argument('latitude', type=str,
                        help='latitude of the starting point')
    parser.add_argument('longitude', type=str,
                        help='longitude of the starting point')
    parser.add_argument('path', type=str, help='path to dataset')
    args = parser.parse_args()

    films_info = read_data(args.path, args.film_year)
    main_location = (int(args.latitude), int(args.longitude))

    usa_list = []
    # add coordinates of the place to the list and remove those which don't have coordinates
    # [name, place, coordinates, distance]
    for film in films_info:
        film_location = get_coordinates(film[1])
        film.append(film_location)
        if film_location is None:
            films_info.remove(film)
            continue
        # add distance from main location to the film place
        distance = haversine(main_location, film_location)
        film.append(distance)

        if 'USA' in film[1]:
            usa_list.append(film)

    # sort films by distance and get 10 shortest
    films_sorted = sorted(films_info, key=lambda x: x[-1])
    closest_films = films_sorted[:10]

    # create a web map with markers of closest films
    text = """<h4>Films information:</h4>
    <i>Films names</i>: {}<br>
    <i>Films locations</i>: {}
    """

    web_map = folium.Map(location=main_location,
                         zoom_start=2)
    iframe = folium.IFrame(html='<h5>You are here</h5>', width=150, height=30)
    web_map.add_child(folium.Marker(location=main_location,
                                    popup=folium.Popup(iframe),
                                    icon=folium.Icon(icon='user', prefix='fa', color='beige')))

    fg_closest = folium.FeatureGroup(
        name=f'Closest film sets in {args.film_year}')
    for film in closest_films:
        iframe = folium.IFrame(html=text.format(
            film[0], film[1]), width=300, height=100)
        fg_closest.add_child(folium.Marker(location=film[-2],
                                           popup=folium.Popup(iframe),
                                           icon=folium.Icon(icon='film',
                                                            prefix='fa',
                                                            color='lightred')))

    # add markers with films created in the same year in the USA
    fg_usa = folium.FeatureGroup(
        name=f'{args.film_year} films located in the USA')
    for film in usa_list:
        iframe = folium.IFrame(html=text.format(
            film[0], film[1]), width=300, height=100)
        fg_usa.add_child(folium.Marker(location=film[-2],
                                       popup=folium.Popup(iframe),
                                       icon=folium.Icon(icon='flag',
                                                        prefix='fa',
                                                        color='darkblue')))
    web_map.add_child(fg_usa)
    web_map.add_child(fg_closest)
    web_map.add_child(folium.LayerControl())
    web_map.save('web_map.html')


if __name__ == '__main__':
    main()
