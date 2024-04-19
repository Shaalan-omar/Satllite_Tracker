import mysql.connector
import streamlit as st

# Connect to the MySQL database
try:
    # Replace 'host', 'user', 'password', and 'database' with your actual credentials
    conn = mysql.connector.connect(
        host='mysql-satellite.alwaysdata.net',
        user='satellite',
        password='Waw.com1',
        database='satellite_db'
    )
    print("Connected to MySQL server")
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit()

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# User input options
options = [
    "Register a user",
    "Create a new list of favorite channels",
    "Show all channels viewable from a certain location",
    "Show user's favorite list coverage",
    "Show top 5 TV Networks/Providers",
    "Show top 5 rockets",
    "Show top 5 growing satellites",
    "Show top 5 channels by language",
    "Show channels filtered by criteria"
]

# Let the user choose an option
user_input = st.sidebar.selectbox("Select an option:", options)

if user_input == "Register a user":
    st.subheader("Enter user data to register")
    
    # Take input values from the user for each column
    username = st.text_input("Enter username:")
    email = st.text_input("Enter email:")
    location = st.text_input("Enter location:")
    gender = st.selectbox("Enter gender:", ["Male", "Female"])
    birthdate = st.date_input("Enter birthdate:")
    region = st.text_input("Enter region:")
    
    if st.button("Insert Data"):
        # Query to insert data into "userr" table
        query = "INSERT INTO userr (Username, Email, Location, Gender, Birthdate, Region) VALUES (%s, %s, %s, %s, %s, %s)"
        
        try:
            # Execute the query with input values
            cursor.execute(query, (username, email, location, gender, birthdate, region))
            conn.commit()  # Commit changes to the database
            st.success("Data inserted successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

elif user_input == "Create a new list of favorite channels":
    st.subheader("Create a new list of favorite channels")
    # Ask user for username and number of channels to add
    username = st.text_input("Enter your username:")
    num_channels = st.number_input("Enter the number of channels to add:", min_value=1, value=1)

    # Loop through and execute inserts based on the number of channels
    for i in range(num_channels):
        channel_name = st.text_input(f"Enter the channel name {i + 1}:")
        button_key = f"add_channel_{i}"  # Unique key for each button
        if st.button("Add Channel", key=button_key):
            try:
                # Query to insert data into "favouritechannel" table
                query = "INSERT INTO favouritechannel (Username, ChNAME) VALUES (%s, %s)"
                cursor.execute(query, (username, channel_name))
                conn.commit()  # Commit changes to the database
                st.success(f"Channel '{channel_name}' added to favorites successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")

elif user_input == "Show all channels viewable from a certain location":
    st.subheader("Channels Viewable from Location")
    
    # Get the longitude of the location from the user
    location_longitude = st.number_input("Enter the longitude of the location:", value=0.0, step=0.1)

    if st.button("Find Channels", key="find_channels_button"):
        # Construct the query to find channels viewable from the location
        query = f"""
            SELECT DISTINCT c.ChName
            FROM chan c
            JOIN satellite s ON c.SatelliteName = s.SatName
            WHERE s.Position BETWEEN {location_longitude - 10} AND {location_longitude + 10}
        """
        
        try:
            # Execute the query
            cursor.execute(query)

            # Fetch all the results
            channels_viewable = cursor.fetchall()

            # Print the results
            st.write("Channels Viewable from Location:")
            for index, channel in enumerate(channels_viewable, start=1):
                st.write(f"{index}. Channel Name: {channel[0]}")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        channels_viewable = cursor.fetchall()

        # Print the results
        st.write("Channels Viewable from Location:")
        for index, channel in enumerate(channels_viewable, start=1):
            st.write(f"{index}. Channel Name: {channel[0]}")


elif user_input == "Show user's favorite list coverage":
    st.subheader("User's favorite list coverage")
    
    # Get username from user input
    username = st.text_input("Enter your username:")

    if st.button("Check Location"):
        # Fetch user's location
        location_query = f"""
            SELECT Location
            FROM userr
            WHERE username = '{username}'
        """
        
        try:
            cursor.execute(location_query)
            user_location = cursor.fetchone()

            if user_location:
                user_location = int(user_location[0])  # Convert to integer
                st.write(f"User '{username}' is located in: {user_location}")

                # Create a view for distinct SatelliteName values for user's channels
                cursor.execute(f"""
                    CREATE VIEW IF NOT EXISTS UserSatelliteNames AS
                    SELECT DISTINCT SatelliteName
                    FROM chan
                    WHERE ChName IN (
                        SELECT ChName
                        FROM favouritechannel
                        WHERE username = '{username}'
                    )
                """)

                # Fetch positions for the fetched satellite names from the view
                positions_query = f"""
                    SELECT SatName, Position
                    FROM satellite
                    WHERE SatName IN (
                        SELECT SatelliteName
                        FROM UserSatelliteNames
                    )
                """
                cursor.execute(positions_query)
                positions = cursor.fetchall()

                # Initialize lists to store coverable and non-coverable satellites
                coverable_satellites = []
                non_coverable_satellites = []

                # Check if user's location is coverable by satellites
                for sat_name, position in positions:
                    position = int(position)
                    if position - 10 <= user_location <= position + 10:
                        coverable_satellites.append(sat_name)
                    else:
                        non_coverable_satellites.append(sat_name)

                # Display coverable and non-coverable satellites
                if coverable_satellites:
                    st.write("Coverable Satellites:")
                    for sat_name in coverable_satellites:
                        st.write(f"- {sat_name} (Coverable)")
                else:
                    st.write("No coverable satellites found.")

                if non_coverable_satellites:
                    st.write("Non-Coverable Satellites:")
                    for sat_name in non_coverable_satellites:
                        st.write(f"- {sat_name} (Non-Coverable)")
                    
                # Fetch FrequencyMagnitude and Encryption for channels
                broadcast_query = f"""
                    SELECT ChName, FrequencyMagnitude, Polarization, Encryptionn
                    FROM broadcast
                    WHERE ChName IN (
                        SELECT ChName
                        FROM favouritechannel
                        WHERE username = '{username}'
                    )
                """
                cursor.execute(broadcast_query)
                channels_info = cursor.fetchall()

                # Display channels' FrequencyMagnitude and Coverability
                st.write("\nChannels Information:")
                for channel_info in channels_info:
                    ch_name, freq_magnitude, polarization, encryption = channel_info
                    if encryption is None or encryption.lower() == "null":
                        st.write(f"- {ch_name}: Frequency Magnitude = {freq_magnitude}, Polarization: {polarization}, Encryption: {encryption} [Coverable]")
                    else:
                        st.write(f"- {ch_name}: Frequency Magnitude = {freq_magnitude}, Polarization: {polarization} , Encryption: {encryption} [Not Coverable]")

            else:
                st.write(f"User '{username}' not found.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")


elif user_input == "Show top 5 TV Networks/Providers":
    st.subheader("Top 5 TV Networks by Number of Channels and Average Satellites per Channel")

    # Execute the query
    query = """
        SELECT 
            TvNetname AS TV_Network,
            COUNT(DISTINCT ChName) AS Number_of_Channels,
            AVG(satellite_count) AS Avg_Satellites_Per_Channel
        FROM 
            (
            SELECT
                TvNetName,
                ChName,
                COUNT(SatelliteName) AS satellite_count
            FROM
                chan
            WHERE
                TvNetname IS NOT NULL AND TvNetname != 'None' 
            GROUP BY
                TvNetName, ChName
        ) AS ChannelSatellites
        GROUP BY
            TvNetName
        ORDER BY
            Number_of_Channels DESC
        LIMIT 5;
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()

        # Display results in a table
        st.table(results)
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")

elif user_input == "Show top 5 rockets":
    st.subheader("Top 5 Rockets by Number of Satellites")

    # Execute the query
    query = """
        SELECT LaunchingRocket, COUNT(SatName) AS SatelliteCount
        FROM satellite
        GROUP BY LaunchingRocket
        ORDER BY SatelliteCount DESC
        LIMIT 5
    """
    try:
        cursor.execute(query)
        top_5_rockets = cursor.fetchall()

        # Display results
        if top_5_rockets:
            for index, rocket in enumerate(top_5_rockets, start=1):
                st.write(f"{index}. {rocket[0]} - {rocket[1]} satellites")
        else:
            st.write("No data available.")
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")

elif user_input == "Show top 5 growing satellites":
    st.subheader("Top 5 Growing Satellites")

    # Execute the query
    query = """
        SELECT s.SatName, s.LaunchDate, COUNT(c.ChName) AS ChannelCount
        FROM satellite s
        JOIN chan c ON s.SatName = c.SatelliteName
        GROUP BY s.SatName, s.LaunchDate
        ORDER BY s.LaunchDate DESC, ChannelCount 
        LIMIT 5
    """
    try:
        cursor.execute(query)
        top_5_growing_satellites = cursor.fetchall()

        # Display results
        if top_5_growing_satellites:
            for index, satellite in enumerate(top_5_growing_satellites, start=1):
                st.write(f"{index}. Satellite Name: {satellite[0]}, Launch Date: {satellite[1]}, Number of Channels: {satellite[2]}")
        else:
            st.write("No data available.")
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")

elif user_input == "Show top 5 channels by language":
    st.subheader("Top 5 Channels for Each Language by Number of Satellites")

    try:
        # Query to show the top 5 channels for each language by the number of satellites they are hosted on
        query = """
            SELECT Language, ChName, SatelliteCount
            FROM (
                SELECT 
                    Language,
                    ChName,
                    COUNT(SatelliteName) AS SatelliteCount,
                    ROW_NUMBER() OVER (PARTITION BY Language ORDER BY COUNT(SatelliteName) DESC) AS rank
                FROM chan
                GROUP BY Language, ChName
            ) AS ChannelSatellites
            WHERE rank <= 5
        """
        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        top_channels_by_language = cursor.fetchall()

        # Display the results
        for index, channel in enumerate(top_channels_by_language, start=1):
            st.write(f"{index}. Language: {channel[0]}, Channel: {channel[1]}, Number of Satellites: {channel[2]}")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
elif user_input == "Show channels filtered by criteria":
    st.subheader("Filter Channels")

    try:
        # Get filter criteria from the user
        region = st.text_input("Enter region (leave empty to skip):").strip()
        satellite = st.text_input("Enter satellite (leave empty to skip):").strip()
        hd_sd = st.text_input("Enter HD/SD (HD/SD/leave empty to skip):").strip()
        language = st.text_input("Enter language (leave empty to skip):").strip()

        # Construct the base query
        query = """
            SELECT t.ChName, t.Language, b.Video AS HD_SD, s.Region AS Region, t.SatelliteName AS Satellite
            FROM chan t
            LEFT JOIN broadcast b ON t.ChName = b.ChName
            LEFT JOIN satellite s ON t.SatelliteName = s.SatName
            WHERE 1
        """

        # Add filters based on user input
        if region:
            query += f" AND s.Region = '{region}'"
        if satellite:
            query += f" AND t.SatelliteName = '{satellite}'"
        if hd_sd:
            query += f" AND b.Video LIKE '%{hd_sd}%'"
        if language:
            query += f" AND t.Language = '{language}'"

        # Execute the query
        cursor.execute(query)
        filtered_channels = cursor.fetchall()

        # Display the results
        if filtered_channels:
            for index, channel in enumerate(filtered_channels, start=1):
                st.write(f"{index}. Channel Name: {channel[0]}, Language: {channel[1]}, HD/SD: {channel[2]}, Region: {channel[3]}, Satellite: {channel[4]}")
        else:
            st.write("No channels found based on the specified filters.")
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")



# Close cursor and connection
cursor.close()
conn.close()
