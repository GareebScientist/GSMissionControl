# Go to `main()` function definition on the bottom and update your N2YO API key 
# and the satellite NORAD ID to track it

import PIL
import matplotlib.pyplot as plt
import numpy as np
import math
import requests
import matplotlib.gridspec as gridspec
import datetime
import os

def get_height(latlng):
    latitude = latlng[0]
    longitude = latlng[1]
    
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        elevation_data = data["results"][0]["elevation"]
        return elevation_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching elevation data: {e}")
        return None

def get_myloc():
    print("Locating this device...")
    url = 'http://ipinfo.io/json'
    response = requests.get(url)
    data = response.json()

    latlng = data['loc'].split(',')
    latlng = [float(d) for d in latlng]
    city = data['city']
    country = data['country']
    region = data['region']
    
    height = get_height(latlng)
    
    return latlng[0], latlng[1], height, city, region, country

def get_sat_data(satellite_id, api_key):  
    print("Fetching satellite data...")  
    (observer_lat, observer_lng, observer_alt, name_city, name_region, name_country) = get_myloc()
    my_loc = (observer_lat, observer_lng, observer_alt, name_city, name_region, name_country)
    
    observer_alt = observer_alt/1e3 # convert from m to km
    seconds = 1; # [Number of future positions to return. Limit 300 seconds]

    # Parameters for the API call
    base_url = 'https://api.n2yo.com/rest/v1/satellite/positions/'
    extended_url = str(satellite_id)+'/'+str(observer_lat)+'/'+str(observer_lng)+'/'+str(observer_alt)+'/'+str(seconds)
    api_key_url = '/&apiKey='+api_key
    
    try:
        response = requests.get(base_url+extended_url+api_key_url)
        response.raise_for_status()  # Check for any errors in the response

        # Parse the JSON data
        data = response.json()
        
        # print(json.dumps(data, indent=2))
        # data['info']
        
        satname = data['info']['satname']
        satid = data['info']['satid']
        transactions = data['info']['transactionscount']
        sat_info = (
            satname, 
            satid, 
            transactions
        )
        
        lat = data['positions'][0]['satlatitude']
        lng = data['positions'][0]['satlongitude']
        alt = data['positions'][0]['sataltitude']
        az = data['positions'][0]['azimuth']
        el = data['positions'][0]['elevation']
        ra = data['positions'][0]['ra']
        dec = data['positions'][0]['dec']
        t = data['positions'][0]['timestamp']
        ecl = data['positions'][0]['eclipsed']
        sat_position = (lat, lng, alt,
                        az, el,
                        ra, dec,
                        t,
                        ecl
        )

        return sat_info, sat_position, my_loc

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def spherical_to_cartesian(r, lat, lng):
    theta = math.radians(90-lat)
    phi = math.radians(lng)
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z

def get_sat_pos(NORAD_id, N2YO_api_key, radius):
    (sat_info, sat_pos, my_loc) = get_sat_data(NORAD_id, N2YO_api_key)

    print("Converting satellite data to required formats...")
    sat_lat = sat_pos[0]
    sat_lng = sat_pos[1]
    sat_alt = sat_pos[2]
    sat_geo_pos = (sat_pos[0:5])
    t = sat_pos[7]
    sat_cart_pos = np.array(spherical_to_cartesian(sat_alt+radius, sat_lat, sat_lng))
    return sat_geo_pos, sat_cart_pos, my_loc, sat_info, t

def plot_sat_pos(NORAD_id, N2YO_api_key, img_save_dir):
    radius = 6371.4 # Radius of Earth in Km
    (sat_geo_pos, sat_cart_pos, my_loc, sat_info, timestamp) = get_sat_pos(NORAD_id, N2YO_api_key, radius)
    
    # Calculate the new width and height of texture image based on the scale factor
    scale_factor = 0.02     
    texture_big = PIL.Image.open('earth.jpg')   # load texture file
    # Texture size is big, so rescale it
    new_width = int(texture_big.width * scale_factor)
    new_height = int(texture_big.height * scale_factor)
    texture = texture_big.resize(
        (new_width, new_height), 
        PIL.Image.Resampling.LANCZOS
    )
    
    # Convert texture to array, divide by 256 to get RGB values that matplotlib accept 
    texture = np.array(texture)/256.
    
    # coordinates of the image - don't know if this is entirely accurate, but probably close
    lons = np.linspace(-180, 180, texture.shape[1]) * np.pi/180 
    lats = np.linspace(-90, 90, texture.shape[0])[::-1] * np.pi/180 
    
    # Create new figure
    print("Creating graphs...")
    fig = plt.figure(dpi=300, facecolor='black', figsize=(7, 6))
    G = gridspec.GridSpec(3, 3)
    
    fig.suptitle('Satellite Current Position - Source: N2YO.com [API]', color="white")
    
    txt_ax = fig.add_subplot(G[1:, 0])  # Annotations
    ax = fig.add_subplot(G[1:, 1:], projection='3d')  # Current position on globe
    ax1 = fig.add_subplot(G[0, 0], projection='polar')  # SkyView
    ax2 = fig.add_subplot(G[0, 1:])  # Ground track
    
    # Make 3D globe surface plot
    x_globe = radius*np.outer(np.cos(lons), np.cos(lats)).T
    y_globe = radius*np.outer(np.sin(lons), np.cos(lats)).T
    z_globe = radius*np.outer(np.ones(np.size(lons)), np.sin(lats)).T
    
    ax.plot_surface(
        x_globe, y_globe, z_globe, 
        rstride=1, 
        cstride=1, 
        facecolors = texture
    )
          
    # Data for three-dimensional satellite position
    vector = sat_cart_pos
    magnitude = np.linalg.norm(vector)
    direction = vector/magnitude
    
    # Create the satellite 3D scatter point and 3D quiver plot
    ax.scatter3D(
        vector[0], vector[1], vector[2], 
        color='red',
        s=20,
        marker='.'
    )
    
    ax.quiver(
        radius*direction[0], radius*direction[1], radius*direction[2], 
        direction[0], direction[1], direction[2], 
        length=magnitude-radius, 
        arrow_length_ratio=0.15,
        color='white',
        linewidth=0.5
    )
    
    # place a text box in upper left in axes coords
    props = dict(boxstyle='round', facecolor='black', alpha=0.5)
    if my_loc[0] > 0:
        lat_suffix = 'N'
    elif my_loc[0] < 0:
        lat_suffix = 'S'
    else:
        lat_suffix = ''
    
    if my_loc[1] > 0:
        lng_suffix = 'E'
    elif my_loc[1] < 0:
        lng_suffix = 'W'
    else:
        lng_suffix = ''
    
    textstr = (
        "\n" + 
        "Your Location: \n" + 
        (my_loc[3] + ", \n") +  
        (my_loc[4] + ", \n") +  
        (my_loc[5] + "\n") + 
        (r'(%.4f°' % (np.abs(my_loc[0]), )) + lat_suffix + (r', %.4f°' % (np.abs(my_loc[1], ))) + lng_suffix + ")\n" +
        str(datetime.datetime.fromtimestamp(timestamp)) + ' Local\n' +
        "\n" + 
        "Satellite: \n" + 
        "Name: " + sat_info[0] + "\n"
        "Visible: " + str(sat_geo_pos[4]>0) + "\n" + 
        (r'Az = %4.2f' % (sat_geo_pos[3], )) + ' °\n' + 
        (r'El = %4.2f' % (sat_geo_pos[4], )) + ' °\n' + 
        (r'Alt = %.2f' % (sat_geo_pos[2], )) + ' Km\n'
    )
    
    txt_ax.text(0, 0.5, textstr, transform=txt_ax.transAxes, fontsize='medium', 
                horizontalalignment='left', verticalalignment='center', 
                bbox=props, color="white", family="monospace"
    )
    
    txt_ax.set_axis_off()               # To set axis visibility to off
    txt_ax.set_facecolor("#3f3e4c")     # To set the background color
    txt_ax.grid(False)                  # To get rid of the grid
   
    # Set the plot props
    ax.set_aspect('equal')          # To set the aspect ratio equal in all axes
    ax.set_axis_off()               # To set axis visibility to off
    ax.set_facecolor("#0F101D")     # To set the background color
    ax.grid(False)                  # To get rid of the grid
    
    # Local Sky View   
    if sat_geo_pos[4] > 0:
        # The satellite is above Horizon - Visible
        ax1.plot(math.radians(sat_geo_pos[3]), 1 - np.abs(sat_geo_pos[4])/90.0, 'r.')
        ax1.set_facecolor("#71c0fc")     # To set the background color
    else:
        # The satellite is below Horizon - Invisible
        ax1.plot(math.radians(sat_geo_pos[3]), 1 - np.abs(sat_geo_pos[4])/90.0, 'r.')
        ax1.set_facecolor("#aa8c72")     # To set the background color
            
    ax1.set_theta_zero_location("N")
    ax1.set_theta_direction(-1)
    ax1.set_xticks(np.linspace(0, 2*np.pi, num=9)[0:-1])  # Less radial ticks
    ax1.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''])
    ax1.set_rmax(1)
    ax1.set_rticks([0, 0.33, 0.67, 1])  # Less radial ticks
    ax1.set_yticklabels([])
    ax1.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
    # Set the color of the theta labels
    theta_labels = ax1.get_xticklabels()
    for label in theta_labels:
        label.set_color('white')  
    
    # Ground Track of Satellite
    sat_img_x = int( ( (sat_geo_pos[1] + 180) / 360.0 ) * texture_big.width )
    sat_img_y = texture_big.height - int( ( (sat_geo_pos[0] + 90) / 180.0 ) * texture_big.height )
    ax2.scatter(
        sat_img_x, sat_img_y, 
        color='red',
        marker='.',
        s=15
    )
    
    # Ground Track of Your Location
    stn_img_x = int( ( (my_loc[1] + 180) / 360.0 ) * texture_big.width )
    stn_img_y = texture_big.height - int( ( (my_loc[0] + 90) / 180.0 ) * texture_big.height )
    ax2.scatter(
        stn_img_x, stn_img_y, 
        color='cyan',
        marker='*',
        s=10
    )
    
    ax2.imshow(texture_big)
    ax2.set_axis_off()               # To set axis visibility to off
    ax2.grid(False)                  # To get rid of the grid
    
    print("Saving file...")
    plt.savefig(img_save_dir)
    # plt.show

def open_image_externally(image_path):
    print("Opening file...")
    try:
        os.startfile(image_path)
    except OSError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def main():
    # Replace `YOUR_API_KEY` with your actual N2YO API key
    # Example: "PCML1-BRZ2M5-QPLW0T-79LK"
    N2YO_api_key = "" # In string type

    # NORAD id of the satellite to track 
    # Example: 57320 (Chandrayaan 3)
    sat_NORAD_id = 57320 # In int type

    img_save_dir = "satellite_dashboard_1.png"

    # Check if inputs are given and then execute the script or throw message
    if ( (N2YO_api_key == "") or (not isinstance(sat_NORAD_id, (float, int))) ):
        print('Please check if `N2YO` API key and the satellite NORAD ID are valid and present!')
        return
    else:
        plot_sat_pos(sat_NORAD_id, N2YO_api_key, img_save_dir)
        open_image_externally(img_save_dir)
        return

if __name__ == "__main__":
    main()