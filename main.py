import streamlit as st
from streamlit_option_menu import option_menu
import requests
from streamlit_lottie import st_lottie
from pathlib import Path
from PIL import Image
import base64
import pickle
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score
import squarify
import mysql.connector
from mysql.connector import Error
import hashlib
import io
import streamlit_authenticator as stauth
import bcrypt
import yaml
import time
from datetime import datetime 
from streamlit_authenticator.utilities.exceptions import (CredentialsError,
                                                      ForgotError,
                                                          LoginError,
                                                          RegisterError,
                                                          ResetError,
                                                          UpdateError)
from io import BytesIO
from streamlit_extras.stylable_container import stylable_container
import re

st.set_page_config(layout="wide")

# Fungsi untuk menghubungkan ke database
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # sesuaikan dengan username MySQL Anda
            password="",  # sesuaikan dengan password MySQL Anda
            database="sukuk"
        )
        # if connection.is_connected():
        #     st.write("Terhubung ke database")
    except Error as e:
        st.write(f"Error: '{e}'")
    return connection

# Fungsi untuk menggunggah file csv ke database

def upload_csv_to_db(dataset_content,user_id,dataset_name):
    connection = create_connection()
    if connection is None:
        return

    try:
        # Baca file CSV
        df = pd.read_csv(dataset_content)

        # Konversi DataFrame menjadi file CSV
        csv_data = df.to_csv(index=False)

        csv_bytes = csv_data.encode('utf-8')
        # dataset_name = csv_data.name

        # Insert data ke tabel
        cursor = connection.cursor()
        query="INSERT INTO data (user_id, dataset, dataset_name, created_at) VALUES (%s, %s, %s,NOW())"
        cursor.execute(query, (user_id, csv_bytes, dataset_name))
        connection.commit()
        cursor.close()
        st.write("File berhasil diunggah ke database")
    except Error as e:
        st.write(f"Error: '{e}'")

# def upload_csv_to_db(file, user_id):
#     connection = create_connection()
#     if connection is None:
#         return

#     try:
#         # Baca file CSV
#         df = pd.read_csv(file)

#         # Konversi DataFrame menjadi file CSV
#         csv_data = df.to_csv(index=False)
#         csv_bytes = csv_data.encode('utf-8')

#         # Insert data ke tabel
#         cursor = connection.cursor()
#         cursor.execute("""
#             INSERT INTO data (user_id, created_at, dataset)
#             VALUES (%s, NOW(), %s)
#         """, (user_id, csv_bytes))
        
#         connection.commit()
#         cursor.close()
#         connection.close()
#         st.write("File berhasil diunggah ke database")
#     except Error as e:
#         st.write(f"Error: '{e}'")

# def save_to_db(user_id, dataset_content, hasil_content, dataset_file):
#     dataset_name = os.path.basename(dataset_file.name)
#     upload_csv_to_db(user_id, dataset_content, dataset_name)

#fungsi untuk mengambil data dari database
def load_data_from_db():
    connection = create_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT dataset FROM data ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            csv_data = result[0]
            df = pd.read_csv(io.StringIO(csv_data.decode('utf-8')))
            return df
        else:
            return None
    except Error as e:
        st.write(f"Error: '{e}'")
        return None

def load_latest_data_from_db(user_id):
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        query = """
            SELECT dataset FROM data
            WHERE user_id = '%s'
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            csv_data = result[0]
            df = pd.read_csv(io.BytesIO(csv_data))
            return df
        else:
            return None
    except Error as e:
        st.write(f"Error: '{e}'")
        return None
    
def save_csv_to_db(user_id, csv_data):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        query = "UPDATE data SET hasil = %s WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        cursor.execute(query, (csv_data, user_id))
        connection.commit()
    except Error as e:
        st.write(f"Error: '{e}'")
    finally:
        cursor.close()
        connection.close()

def get_history_from_db(user_id):
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, created_at, dataset_name FROM data WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        history = cursor.fetchall()
        cursor.close()
        return history
    except Error as e:
        st.error(f"Error fetching data: {e}")
        return None
    finally:
        connection.close()

def delete_data_from_db(data_id):
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        query = "DELETE FROM data WHERE id = %s"
        cursor.execute(query, (data_id,))
        connection.commit()
        cursor.close()
    except Error as e:
        st.error(f"Error deleting data: {e}")
    finally:
        connection.close()

# Fungsi untuk mengambil data dari kolom BLOB dalam database MySQL
def get_blob_data(data_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT hasil FROM data WHERE id = %s", (data_id,))
    result = cursor.fetchone()
    blob_data = result[0] if result else None
    cursor.close()
    connection.close()
    return blob_data


# Fungsi untuk membuat tombol unduh
def create_download_button(blob_data, filename):
    if blob_data is not None:
        # Konversi blob_data menjadi DataFrame
        try:
            df = pd.read_csv(io.BytesIO(blob_data))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        # Menyimpan DataFrame ke dalam file CSV
        csv_data = df.to_csv(index=False)

        with stylable_container(
            "green",
            css_styles=["""
                button {
                    background-color: #008000;
                    color: white;
                }
                button:hover {
                    background-color: white;
                    color: #008000;
                }
            """]
        ):
            download_button = st.download_button(
                label="Unduh Hasil",
                data=csv_data,
                file_name=filename,
                mime='text/csv',
                
            )


        # st.markdown("""
        # <style>
        # .custom-table-row-buttons .download-btn {
        #     background-color: #4CAF50;
        #     color: white;
        # }
        # </style>
        # """, unsafe_allow_html=True)

        # # Tawarkan file CSV untuk diunduh dengan tombol unduh
        # st.download_button(
        #     label="Unduh Hasil",
        #     data=csv_data,
        #     file_name=filename,
        #     mime='text/csv',
        #     css_class="download-btn"
        # )
    else:
        st.warning("Tidak ada data untuk diunduh")
# def create_download_button(data, filename):
#     if data is not None:
#         csv_data = data.decode('utf-8')
#         csv_data = csv_data.splitlines()
#         csv_data = [row.split(',') for row in csv_data]
#         st.download_button(
#             label="Unduh Data",
#             data=pd.DataFrame(csv_data),
#             file_name=filename,
#             mime='text/csv'
#         )
#     else:
#         st.warning("Tidak ada data untuk diunduh")

# Fungsi untuk melihat detail data
def get_detail_from_db(data_id):
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT hasil FROM data WHERE id = %s"
        cursor.execute(query, (data_id,))
        detail = cursor.fetchone()
        cursor.close()
        return detail['hasil']
    except Error as e:
        st.error(f"Error fetching detail: {e}")
        return None
    finally:
        connection.close()

def create_download_link(data_id, data):
    try:
        csv = data.to_csv(index=False).encode('utf-8')
        return csv
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return None

# Fungsi untuk mengambil pengguna dari database
def fetch_users():
    connection = create_connection()
    if connection is None:
        return {}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, password, email FROM users")
        result = cursor.fetchall()
        cursor.close()
        connection.close()

        users = {}
        for row in result:
            users[row["username"]] = {
                "name": row["username"],
                "password": row["password"],
                "email": row["email"]
            }
        return users
    except Error as e:
        st.write(f"Error: '{e}'")
        return {}

# Fungsi untuk menambahkan pengguna baru ke database
def add_user(username, password, email):
    connection = create_connection()
    if connection is None:
        return

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        connection.commit()
        cursor.close()
        connection.close()
        st.write("Pengguna berhasil ditambahkan")
    except Error as e:
        st.write(f"Error: '{e}'")



# Fetch users from the database
users = fetch_users()

# Create authentication object
credentials = {"usernames": {}}

for username, info in users.items():
    credentials["usernames"][username] = {
        "name": username,
        "password": info["password"],
        "email": info["email"]
    }

# Create a YAML configuration for the authenticator
config = {
    "credentials": credentials,
    "cookie": {
        "name": "streamlit_auth",
        "expiry_days": 30
    },
    "preauthorized": {}
}

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    "abcdef",  # secret key
    config["cookie"]["expiry_days"],
    config["preauthorized"]
)

# Fungsi untuk logout
def logout(authenticator):
    authenticator.logout()

# Mendapatkan waktu saat ini sebagai kunci unik
button_key = f"logout_button_{time.time()}"

def is_valid_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

# Add sign up functionality
def signup_page():
    st.title("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if not is_valid_email(email):
            st.error("Email tidak valid")
        elif password != password_confirm:
            st.error("Passwords tidak sesuai")
        else:
            add_user(username, password, email)
            st.success("Sign up sukses. Silakan log in.")


def get_user_id(username):
    connection = create_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        query = "SELECT id FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return result[0]
        else:
            return None
    except Error as e:
        st.write(f"Error: '{e}'")
        return None
# Fungsi untuk mengambil profil pengguna dari database
def get_user_profile(username):
    connection = create_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, email, password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return result
        else:
            return None
    except Error as e:
        st.write(f"Error: '{e}'")
        return None

# Fungsi untuk mengupdate profil pengguna di database
def update_user_profile(username, new_email, new_password):
    connection = create_connection()
    if connection is None:
        return

    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE users 
            SET  email = %s, password = %s 
            WHERE username = %s
        """, (new_email, hashed_password, username))
        connection.commit()
        cursor.close()
        connection.close()
        st.write("Profil berhasil diperbarui")
    except Error as e:
        st.write(f"Error: '{e}'")

# Add forgot password functionality
def forgot_password_page():
    st.title("Forgot Password")
    try:
        username, email, new_random_password = authenticator.forgot_password()
        if username:
            reset_password(username, new_random_password)
            st.success('New password sent securely')
        else:
            st.error('Username not found')
    except ForgotError as e:
        st.error(e)

# Halaman profil
def profile_page(username):
    st.write("## Profil Saya")

    profile_data = get_user_profile(username)
    if profile_data:
        st.markdown("""
            <style>
                .stTextInput>div>div>input[disabled] {
                    color: black !important;
                }
                .stTextInput>label {
                    color: black !important;
                }
            </style>
        """, unsafe_allow_html=True)
        new_username = st.text_input("Username", value=profile_data['username'], disabled=True)
        new_email = st.text_input("Email", value=profile_data['email'])
        new_password = st.text_input("Password", type="password")
        new_password_confirm = st.text_input("Confirm Password", type="password")

        if st.button("Update Profil"):
            if new_password != new_password_confirm:
                st.error("Passwords do not match")
            else:
                update_user_profile(username, new_email, new_password)
                st.success("Profil berhasil diperbarui. Silakan login kembali dengan informasi baru Anda.")
                st.experimental_rerun()
    else:
        st.error("Gagal memuat profil pengguna.")

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code !=200:
        return None
    return r.json()

# lottie_coder = load_lottieurl("https://lottie.host/fd35fe7a-1d7e-44e9-a387-060d689f6d78/XmGvW2kOzb.json")

# Main app
# Main app
def main():
    # selected = st.sidebar.selectbox("Pilih halaman", options=["Login", "Sign Up"])

    # if selected == "Sign Up":
    #     signup_page()
    # else:
    
    
    # Fungsi untuk membaca gambar dan mengonversinya ke format base64
    def read_image(filename):
        with open(filename, "rb") as f:
            image_data = f.read()
            encoded_image = base64.b64encode(image_data).decode("utf-8")
        return encoded_image

    # Path ke file gambar logo.png di folder assets
    logo_path = "assets/logo.png"

    # Membaca gambar dan mengonversi ke base64
    logo_base64 = read_image(logo_path)

    # Menampilkan gambar di sidebar dengan CSS untuk posisi tengah
    st.sidebar.markdown(
        f'<p style="text-align:center;"><img src="data:image/png;base64,{logo_base64}" alt="logo" width="150"></p>',
        unsafe_allow_html=True
    )

    utama = st.sidebar.selectbox("Pilih halaman", options=["Login", "Sign Up"])
    if utama == "Sign Up":
        signup_page()
    elif utama == "Login":
        name, authentication_status, username = authenticator.login(fields={"Username": "Username", "Password": "Password"})
        
        if authentication_status is False:
            st.error("Username atau password salah")
        elif authentication_status is None:
            st.warning("Silakan masukkan username dan password Anda")
        elif authentication_status:
            st.sidebar.write(f"Welcome *{name}*")

            # Rest of your code for Beranda
            # Kode aplikasi utama dimulai dari sini


            images = [
                "clustering.png",
                "profilRisiko.png",
                "alat.png",
                "silhouette.png",
                "history.png",
                "input.png",
                "hasil.png",
                "dbi.png",
            ]

            base64_images = []

            # Membaca dan mengubah setiap gambar menjadi format base64
            for image in images:
                with open(f"assets/{image}", "rb") as file:
                    image_data = file.read()
                    data_url = base64.b64encode(image_data).decode("utf-8")
                    base64_images.append(f'<img src="data:image/png;base64,{data_url}" alt="{image}">')

            # Memasukkan hasil ke dalam variabel yang sesuai
            clustering, profilRisiko, alat, silhouette, riwayat, input, hasil, dbi, = base64_images

            
            with st.sidebar.container():
                Menu = option_menu(
                    menu_title = None,
                    options = ['Beranda','Klaster', 'Riwayat', 'Profil'],
                    icons = ['house-fill','tools','ticket-detailed','person-badge'],
                    orientation="vertical"
                    )

            authenticator.logout("Logout", "sidebar")

            if Menu == 'Beranda':
                # Kode CSS untuk mengatur tampilan kotak
                col1, col2, col3 = st.columns([2.5, 1, 2.5])
                with col2:
                    st.write("## Clustering Sukuk")
                    st.write("###")
                col4, col5, col6 = st.columns([2, 2, 2])
                with col4:
                    konten1= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="border: 0;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {clustering}
                                </td>
                                <td style="border: 0;"><b>K-Means Clustering</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">K-Means Clustering adalah metode pengelompokan data yang membagi dataset menjadi k kelompok berdasarkan pola atau kesamaan karakteristiknya.</td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.markdown(konten1, unsafe_allow_html=True)

                with col5:
                    konten2= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="margin: 0 auto; border: 0; text-align: left; font-size: 20px;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {silhouette}
                                </td>
                                <td style="border: 0;"><b>Nilai Silouette</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">Nilai Silhouette digunakan untuk menentukan jumlah kelas yang optimal dalam clustering; semakin tinggi nilai Silhouette, semakin baik klaster yang terbentuk.
                                </td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.markdown(konten2, unsafe_allow_html=True)
                
                with col6:
                    konten3= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="border: 0;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {alat}
                                </td>
                                <td style="border: 0;"><b>Klaster</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">Menu Klaster dapat kamu gunakan untuk menganalisis sukuk yang kamu inginkan dan  memberikan berbagai informasi dan insight berdasarkan data yang telah dimasukkan.</td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.markdown(konten3, unsafe_allow_html=True)
                
                col7, col8, col9 = st.columns([2, 2, 2])
                with col7:
                    konten4= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="border: 0;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {riwayat}
                                </td>
                                <td style="border: 0;"><b>Riwayat</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">Menu riwayat memungkinkan melihat kembali data yang pernah diproses sebelumnya sehingga memudahkan dalam mengakses hasil analisis tanpa perlu memasukkan data ulang.</td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.markdown(konten4, unsafe_allow_html=True)
                
                with col8:
                    konten5= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="border: 0;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {input}
                                </td>
                                <td style="border: 0;"><b>Input Data</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">Data yang dimasukkan harus dalam format CSV dengan kolom:nama sukuk, nilai nominal (milyar rupiah), interest/disc rate, listing date, dan mature date.</td>
                        </table>
                    </div>
                    """
                    st.markdown(konten5, unsafe_allow_html=True)

                with col9:
                    konten6= f"""
                    <style>
                    .button {{
                        color: #ffffff;
                        padding: 10px 20px;
                        text-align: right;
                        text-decoration: none;
                        display: inline-block;
                        border-radius: 5px;
                        transition-duration: 0.4s;
                        cursor: pointer;
                    }}
                    .button:hover {{
                        border-radius: 5px;
                        background-color:#ff4b4b;
                        border-color: #ff4b4b;
                    }}
                    .container{{
                        text-align: center;
                    }}
                    .box-container {{
                        display: inline-block;
                        justify-content: space-between;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .box {{
                        display: inline-block;
                        align-items: center;
                        justify-content: space-between;
                        width: 90%;
                        max-width: 600px;
                        height:90%;
                        padding: 10px;
                        margin-bottom: 20px;
                        border: 2px solid;
                        transition: all 0.3s ease;
                        border-radius: 10px;
                        border-color: #262730;
                    }}

                    .box:hover {{
                        border-color: #ff4b4b;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                    }}

                    .box img {{
                        width: 80px;
                        height: auto;
                        margin-right: 20px;
                    }}

                    .box p {{
                        margin: 5px;
                        font-size: 16px;
                        text-align: left;
                    }}
                    table {{
                        margin: 0 auto;
                        border: transparent;
                        text-align: left;
                        font-size: 20px;
                    }}
                    tr {{
                        border: black;
                    }}
                    td {{
                        border: transparent;
                    }}
                    .selectbox-dropdown {{
                    border-color: #3498db;
                    border-radius: 5px;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    color: #3498db;
                    font-weight: bold;
                    }}
                    </style>

                    <div class="box">
                        <table style="border: 0;">
                            <tr style="border: 0;">
                                <td rowspan="2" style="border: 0;">
                                    {hasil}
                                </td>
                                <td style="border: 0;"><b>Hasil Perhitungan</b></td>
                            </tr>
                            <tr style="border: 0;">
                                <td style="border: 0;">Hasil perhitungan akan menampilkan berbagai statistik data yang telah diolah. Meskipun begitu, hanya jenis klaster yang dihasilkan dari analisis data tersebut yang akan disimpan.</td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.markdown(konten6, unsafe_allow_html=True)
                
                # col27, col28, col29 = st.columns([2, 2, 2])
                # with col28:
                #     konten7= f"""
                #     <style>
                #     .button {{
                #         color: #ffffff;
                #         padding: 10px 20px;
                #         text-align: right;
                #         text-decoration: none;
                #         display: inline-block;
                #         border-radius: 5px;
                #         transition-duration: 0.4s;
                #         cursor: pointer;
                #     }}
                #     .button:hover {{
                #         border-radius: 5px;
                #         background-color:#ff4b4b;
                #         border-color: #ff4b4b;
                #     }}
                #     .container{{
                #         text-align: center;
                #     }}
                #     .box-container {{
                #         display: inline-block;
                #         justify-content: space-between;
                #         margin-bottom: 20px;
                #         border-radius: 5px;
                #     }}
                #     .box {{
                #         display: inline-block;
                #         align-items: center;
                #         justify-content: space-between;
                #         width: 90%;
                #         max-width: 600px;
                #         height:90%;
                #         padding: 10px;
                #         margin-bottom: 20px;
                #         border: 2px solid;
                #         transition: all 0.3s ease;
                #         border-radius: 10px;
                #         border-color: #262730;
                #     }}

                #     .box:hover {{
                #         border-color: #ff4b4b;
                #         cursor: pointer;
                #         box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
                #     }}

                #     .box img {{
                #         width: 80px;
                #         height: auto;
                #         margin-right: 20px;
                #     }}

                #     .box p {{
                #         margin: 5px;
                #         font-size: 16px;
                #         text-align: left;
                #     }}
                #     table {{
                #         margin: 0 auto;
                #         border: transparent;
                #         text-align: left;
                #         font-size: 20px;
                #     }}
                #     tr {{
                #         border: black;
                #     }}
                #     td {{
                #         border: transparent;
                #     }}
                #     .selectbox-dropdown {{
                #     border-color: #3498db;
                #     border-radius: 5px;
                #     padding: 5px 15px;
                #     background-color: #ecf0f1;
                #     color: #3498db;
                #     font-weight: bold;
                #     }}
                #     </style>

                #     <div class="box">
                #         <table style="border: 0;">
                #             <tr style="border: 0;">
                #                 <td rowspan="2" style="border: 0;">
                #                     {dbi}
                #                 </td>
                #                 <td style="border: 0;"><b>Calinski-Harabasz Index (CHI)</b></td>
                #             </tr>
                #             <tr style="border: 0;">
                #                 <td style="border: 0;">Calinski-Harabasz Index membantu kita memahami seberapa bagus kelompok-kelompok yang dibentuk oleh algoritma clustering. Semakin tinggi nilai indeksnya, semakin baik hasil clusteringnya.</td>
                #             </tr>
                #         </table>
                #     </div>
                #     """
                #     st.markdown(konten7, unsafe_allow_html=True)

            elif Menu == 'Klaster':
                def load_data(uploaded_file):
                    if uploaded_file is not None:
                        st.success("File berhasil diunggah!")
                        df = pd.read_csv(uploaded_file)
                        df['Listing Date'] = pd.to_datetime(df['Listing Date'])#format='%d %b %Y')
                        df['Mature Date'] = pd.to_datetime(df['Mature Date']) #format='%d %b %Y')
                        st.session_state['df'] = df
                        return df
                    else:
                        st.write("Silakan unggah file data untuk diproses.")
                        return None

                # Fungsi untuk membuat tautan unduhan CSV
                def csv_download_link(df, csv_file_name, download_link_text):
                    csv_data = df.to_csv(index=True)
                    b64 = base64.b64encode(csv_data.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="{csv_file_name}">{download_link_text}</a>'
                    st.markdown(href, unsafe_allow_html=True)    
                # Initializing session state variables
                if 'df' not in st.session_state:
                    st.session_state['df'] = None

                if 'uploaded_file' not in st.session_state:
                    st.session_state['uploaded_file'] = None
                    # Fungsi untuk membuat tautan unduhan CSV

                # Membuat kembali model dan cluster_stats
                with open('kmeans_model.pkl', 'rb') as f:
                    model= pickle.load(f) #cluster_stats 
                st.write("## Halaman Perhitungan Algoritma K-Means")
                submenu = st.selectbox(
                    'Pilih Opsi', ['Input Data','Praproses', 'Pemodelan', 'Prediksi'], #
                        format_func=lambda x: f"{x}"
                    )

                if submenu == 'Input Data':
                            
                    if 'user_id' not in st.session_state:
                        user_id = get_user_id(username)
                        if user_id:
                            st.session_state['user_id'] = user_id
                        else:
                            st.error("User ID tidak ditemukan")
                    
                    # Jika pengguna sudah login, lanjutkan ke bagian unggah file
                    st.write("###### Pastikan Datamu berformat CSV & memiliki kolom Nama Sukuk, Nilai Nominal (Milyar Rupiah), Interest/Disc Rate, Listing Date, dan Mature Date")
                    # Dataframe contoh
                    contoh = {
                        'Nama Sukuk': ['SUKUK IJARAH BERKELANJUTAN I ANGKASA PURA I TAHAP I TAHUN 2021 SERI B', 'SUKUK IJARAH BERKELANJUTAN III PLN TAHAP V TAHUN 2019 SERI C', 'SUKUK IJARAH BERKELANJUTAN I MORATELINDO TAHAP II TAHUN 2020 SERI A'],
                        'Nilai Nominal (Milyar Rupiah)': [215, 92, 191],
                        'Interest/disc rate (%)': ['7,1', '8,6', '10,5'],
                        'Listing Date': ['09 September 2021', '02 Oktober 2019', '12 Agustus 2020'],
                        'Mature Date': ['08 September 2026', '01 Oktober 2029', '11 Agustus 2023']
                    }

                    cth = pd.DataFrame(contoh)

                    # Tampilkan dataframe menggunakan Streamlit
                    st.write("##### Contoh Data")
                    st.write(cth)
                    uploaded_file = st.file_uploader("Pilih file", type=['csv'])
                    

                    if uploaded_file is not None:
                        if st.button("Upload"):
                            dataset_name = uploaded_file.name  # Ambil nama file
                            upload_csv_to_db(uploaded_file, st.session_state['user_id'], dataset_name)
                            st.session_state['uploaded_file'] = True
                            df = load_latest_data_from_db(st.session_state['user_id'])
                            if df is not None:
                                st.write("### Tinjauan Data")
                                st.write("Jumlah baris:", df.shape[0])
                                st.write("Jumlah kolom:", df.shape[1])
                                st.write("Lima baris pertama dari data:")
                                st.write(df.head())
                            else:
                                st.write("Tidak ada data yang tersedia di database")
                    else:
                        st.write("Silakan pilih file CSV untuk diunggah")
                    
                elif submenu == 'Praproses':
                    if 'user_id' not in st.session_state:
                        user_id = get_user_id(username)
                        if user_id:
                            st.session_state['user_id'] = user_id
                        else:
                            st.error("User ID tidak ditemukan")
                        
                    if 'uploaded_file' in st.session_state and st.session_state['uploaded_file']:
                        st.write("### Pembersihan Data")
                        
                        df = load_latest_data_from_db(st.session_state['user_id'])
                        if df is not None:
                            st.session_state['data'] = df
                            # 1. Handling missing, null, and duplicate values
                            st.write("Jumlah missing values:")
                            st.write(df.isnull().sum())

                            # st.write("Jumlah NA values:")
                            # st.write((df == 'NA').sum())

                            st.write("Jumlah baris yang duplikat:", df.duplicated().sum())

                            # Providing options for handling missing and duplicate values
                            if st.checkbox('Hapus baris yang duplikat'):
                                df.drop_duplicates(inplace=True)
                                st.write("Baris duplikat telah dihapus.")
                        
                            if st.checkbox('Hapus baris yang missing value'):
                                df.replace('NA', pd.NA, inplace=True)
                                df.dropna(inplace=True)
                                st.write("Baris dengan yang missing value telah dihapus.")

                            data = df
                            st.session_state['df'] = data

                            # # Visualisasi distribusi tanggal menggunakan histogram
                            # st.subheader("Distribusi Tanggal")
                            # fig, ax = plt.subplots()
                            # sns.histplot(data["Listing Date"], bins=20, ax=ax)
                            # plt.xticks(rotation=45)
                            # st.pyplot(fig)

                            # Analisis tren seiring waktu menggunakan data tanggal
                            # st.subheader("Analisis Tren Seiring Waktu")
                            # Ubah format tanggal menjadi datetime jika diperlukan
                            data["Listing Date"] = pd.to_datetime(data["Listing Date"])
                            data["Mature Date"] = pd.to_datetime(data["Mature Date"])
                            # Ekstrak tahun dari kolom tanggal
                            data["Listing Year"] = data["Listing Date"].dt.year
                            data["Mature Year"] = data["Mature Date"].dt.year
                            # Hitung jumlah sukuk yang terdaftar dan jatuh tempo tiap tahun
                            listing_year_counts = data["Listing Year"].value_counts().sort_index()
                            mature_year_counts = data["Mature Year"].value_counts().sort_index()
                            # # Plot tren
                            # fig, ax = plt.subplots()
                            # ax.plot(listing_year_counts.index, listing_year_counts.values, label="Sukuk Terdaftar")
                            # ax.plot(mature_year_counts.index, mature_year_counts.values, label="Sukuk Jatuh Tempo")
                            # ax.set_xlabel("Tahun")
                            # ax.set_ylabel("Jumlah Sukuk")
                            # ax.legend()
                            # st.pyplot(fig)

                    else:
                        st.write("Tidak ada data yang tersedia. Silakan unggah file di bagian 'Input Data'.")

                elif submenu == 'Pemodelan':
                    st.write("### Pemodelan dengan KMeans")
                    if 'user_id' not in st.session_state:
                        user_id = get_user_id(username)
                        if user_id:
                            st.session_state['user_id'] = user_id
                        else:
                            st.error("User ID tidak ditemukan")
                    if 'data' in st.session_state:
                        df = st.session_state['df']
                        excludeColumn = ['Listing Year', 'Mature Year']
                        df = df.drop(excludeColumn, axis=1)
                        col10, col11 = st.columns(2)  # Membuat dua kolom dengan lebar yang sama

                        with col10:
                            st.write("#### Data sebelum dilakukan clustering")
                            st.write(df)
                        # # Mengkonversi kolom 'Nilai Nominal' ke tipe data string
                        # df['Nilai Nominal'] = df['Nilai Nominal'].astype(str)
                        # # Menghapus koma (',') dari kolom 'Nilai Nominal' dan mengonversi ke float
                        # df['Nilai Nominal'] = df['Nilai Nominal'].str.replace(',', '').astype(float)
                        # # Memperbarui kolom Nilai Nominal dengan nilai yang sudah dibagi oleh 1 miliar
                        # df['Nilai Nominal'] = df['Nilai Nominal'] / 1000000000
                        # # Mengubah nama kolom menjadi "Nilai Nominal (Billion)"
                        # df.rename(columns={'Nilai Nominal': 'Nilai Nominal (Billion Rp)'}, inplace=True)
                        # # Mengubah nama kolom "Interest/ Disc rate" menjadi "Interest/ Disc rate (%)"
                        # df = df.rename(columns={'Interest/ Disc rate': 'Interest/ Disc rate (%)'})
                        # Mengubah kolom 'Listing Date' dan 'Mature Date' menjadi tipe data datetime
                        df['Listing Date'] = pd.to_datetime(df['Listing Date'], format='%d %b %Y')
                        df['Mature Date'] = pd.to_datetime(df['Mature Date'], format='%d %b %Y')
                        # Menghitung selisih bulan antara 'Listing Date' dan 'Mature Date'
                        df['Effective Date (Month)'] = ((df['Mature Date'] - df['Listing Date']) / pd.Timedelta(days=30)).astype(int)
                        # Menghapus kolom
                        excludeColumn = ['Listing Date', 'Mature Date']
                        dfSorted = df.drop(excludeColumn, axis=1)
                
                        # st.write(dfSorted)

                        # Normalisasi
                        # Inisialisasi MinMaxScaler
                        scaler = MinMaxScaler()
                        # Fit dan transformasi data numerik
                        numerical_features = dfSorted.columns[1:]  # Mengambil fitur-fitur numerik
                        dfNormalized = dfSorted.copy()  # Membuat salinan dataframe
                        dfSorted[numerical_features] = dfSorted[numerical_features].replace(',', '', regex=True).astype(float)
                        # Normalisasi fitur-fitur numerik
                        dfNormalized[numerical_features] = scaler.fit_transform(dfSorted[numerical_features])
                            
                        #st.write(dfNormalized)

                        X = dfNormalized[['Nilai Nominal (Billion Rp)', 'Interest/ Disc rate (%)', 'Effective Date (Month)']]
                        # Jumlah klaster yang akan dicoba
                        n_clusters_range = range(2, 11)
                        # List untuk menyimpan skor Silhouette
                        silhouette_scores = []
                        # Melakukan clustering dan menghitung skor Silhouette untuk setiap jumlah klaster
                        for n_clusters in n_clusters_range:
                            # Inisialisasi dan melakukan clustering menggunakan KMeans
                            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                            cluster_labels = kmeans.fit_predict(X)

                            # Menghitung skor Silhouette
                            silhouette_avg = silhouette_score(X, cluster_labels)
                            silhouette_scores.append(silhouette_avg)

                            # Menampilkan nilai Silhouette Coefficient untuk setiap nilai k
                            print(f"Jumlah klaster (k={n_clusters}): Silhouette Coefficient = {silhouette_avg}")

                        # Membuat plot dengan ukuran yang lebih kecil
                        fig, ax = plt.subplots(figsize=(6, 4))  # Ubah ukuran sesuai kebutuhan Anda
                        ax.plot(n_clusters_range, silhouette_scores, marker='o')
                        ax.set_title('Skor Silhouette untuk Jumlah Klaster yang Berbeda')
                        ax.set_xlabel('Jumlah Klaster')
                        ax.set_ylabel('Silhouette Score')
                        ax.set_xticks(n_clusters_range)
                        ax.grid(True)

                        # Mengatur layout streamlit menggunakan st.columns
                        
                            

                        with col11:
                            st.pyplot(fig)  # Menampilkan grafik di kolom pertama
                            st.write("#### Jumlah klaster paling optimal adalah klaster yang memiliki nilai sillhouette paling tinggi")

                        # Allow the user to select the number of clusters k
                        n_clusters = st.number_input('Pilih jumlah klaster k dari 2 hingga 20:', min_value=2, max_value=20, value=3, step=1, key="cluster_value")
                        st.write(f'Anda telah memilih untuk membagi menjadi {n_clusters} klaster.')

                        # Apply the KMeans model with the selected number of clusters
                        model = KMeans(n_clusters=n_clusters, random_state=42)
                        # Melakukan clustering
                        model.fit(X)
                        # Menambahkan kolom 'Cluster' ke DataFrame untuk menyimpan hasil clustering
                        df['Cluster'] = model.labels_

                        col12, col13, col14 = st.columns([0.25,2,0.25])
                        with col13:
                            st.write(df)

                        df_sub = df.copy() #dfSorted
                        df_sub['Cluster'] = model.labels_  
                        cluster_stats = df_sub.groupby('Cluster').agg({
                            'Effective Date (Month)': 'mean',
                            'Nilai Nominal (Billion Rp)': 'mean',
                            'Interest/ Disc rate (%)': ['mean', 'count']
                        }).round(2)

                        # Mengganti nama kolom pada DataFrame cluster_stats
                        cluster_stats.columns = ['Rerata_Effective Date (Month)', 'Rerata_Nilai Nominal (Billion Rp)', 'Rerata_Interest/ Disc rate (%)','Count']

                        # Menghitung persentase dari masing-masing jumlah cluster
                        cluster_stats['Persentase'] = (cluster_stats['Count'] / cluster_stats['Count'].sum() * 100).round(2)

                        # Mengatur ulang indeks agar kolom 'Cluster' menjadi kolom biasa, bukan indeks
                        cluster_stats.reset_index(inplace=True)

                        # Mengubah nama kelompok klaster agar lebih mudah dibaca
                        cluster_stats['Cluster'] = 'Cluster ' + cluster_stats['Cluster'].astype('str')

                        # Menampilkan subjudul "Statistik untuk Setiap Klaster"
                        st.subheader('Statistik untuk Setiap Klaster')
                        
                        col15, col16 = st.columns(2)  # Membuat dua kolom dengan lebar yang sama

                        with col15:
                            # Menampilkan DataFrame cluster_stats
                            st.write("###")
                            st.write("###")
                            st.write("###")
                            st.write("###")
                            st.dataframe(cluster_stats)
                        with col16:
                            # Grafik Scatter
                            fig_scatter = px.scatter(
                                cluster_stats,
                                x='Rerata_Nilai Nominal (Billion Rp)',
                                y='Rerata_Interest/ Disc rate (%)',
                                size='Rerata_Effective Date (Month)',
                                color='Cluster',
                                log_x=True,
                                size_max=60
                            )
                            # Menampilkan grafik Scatter
                            st.plotly_chart(fig_scatter, use_container_width=True)

                        col17, col18 = st.columns(2)  # Membuat dua kolom dengan lebar yang sama

                        with col17:
                            # Diagram Pohon
                            # Mengatur warna untuk setiap cluster - Anda dapat mengubah ini sesuai keinginan Anda
                            colors_dict = {
                                0: 'green',
                                1: 'red',
                                2: 'royalblue',
                                3: 'orange',
                                4: 'purple'
                            }
                            fig_treemap, ax_treemap = plt.subplots()  # Membuat objek fig dan ax terpisah untuk diagram Pohon
                            fig_treemap.set_size_inches(14, 10)

                            squarify.plot(sizes=cluster_stats['Count'], 
                                        label=[f'Cluster {i}\n{row["Rerata_Nilai Nominal (Billion Rp)"]} milyar\n{row["Rerata_Interest/ Disc rate (%)"]} imbal hasil\n{row["Rerata_Effective Date (Month)"]} bulan\n{row["Count"]} sukuk ({row["Persentase"]}%)' 
                                                for i, row in cluster_stats.iterrows()],
                                        color=[colors_dict.get(cluster) for cluster in cluster_stats.index],
                                        alpha=0.6,
                                        text_kwargs={'fontsize':12, 'fontweight':'bold'})

                            ax_treemap.set_title("Cluster Sukuk", fontsize=26, fontweight="bold")
                            ax_treemap.axis('off')
                            st.pyplot(fig_treemap)

                        with col18:
                            # Membuat 3D scatter plot
                            fig_3d = px.scatter_3d(
                                cluster_stats,
                                x='Rerata_Nilai Nominal (Billion Rp)',
                                y='Rerata_Interest/ Disc rate (%)',
                                z='Rerata_Effective Date (Month)',
                                color='Cluster',
                                size='Count',
                                labels={'Rerata_Nilai Nominal (Billion Rp)': 'Nilai Nominal (Billion Rp)', 'Rerata_Interest/ Disc rate (%)': 'Interest/ Disc rate (%)', 'Rerata_Effective Date (Month)': 'Effective Date (Month)'}
                            )

                            st.plotly_chart(fig_3d, use_container_width=True)

                        # Konversi DataFrame ke CSV
                        csv = df.to_csv(index=False)
                        col19, col20, col21 = st.columns((1,1,1))
                        with col19:
                            # Membuat tombol untuk menyimpan CSV
                            if st.button('Simpan Hasil', use_container_width=True):
                                save_csv_to_db(st.session_state['user_id'], csv)
                                st.success('CSV berhasil disimpan!')

                        # save_csv_to_db(st.session_state['user_id'], csv)
                        with col20:
                        # Membuat tombol unduh
                            st.download_button(
                                label="Unduh hasil clustering",
                                data=csv,
                                file_name='hasil clustering.csv',
                                mime='text/csv',
                                use_container_width=True
                            )
                        
                        with col21:
                        # Menambahkan tombol untuk mengekspor model
                            # if st.button('Ekspor Model', use_container_width=True):
                            #     # # Menyimpan model ke dalam file .pkl
                            #     # with open('kmeans_model.pkl', 'wb') as f:
                            #     #     pickle.dump((model, cluster_stats), f)
                                
                            #     # st.session_state.model_exported = True
                            #     # st.write('Model (kmeans_model.pkl) telah berhasil diekspor!')
                                buffer = BytesIO()
                                pickle.dump((model, cluster_stats), buffer)
                                buffer.seek(0)  # Reset buffer position to the beginning

                                # Buat tombol unduh
                                st.download_button(
                                    label="Unduh Model",
                                    data=buffer,
                                    file_name='kmeans_model.pkl',
                                    mime='application/octet-stream',
                                    use_container_width=True
                                )

                    else:
                        st.write("Tidak ada data yang tersedia. Silakan unggah file di bagian 'Input Data'.")
                elif submenu == 'Prediksi':
                    # if 'model_exported' in st.session_state and st.session_state.model_exported:
                    #     # Memuat kembali model dan cluster_stats
                    #     with open('kmeans_model.pkl', 'rb') as f:
                    #         model, cluster_stats = pickle.load(f)

                    #     st.subheader('Statistik untuk Setiap Klaster')
                    #     st.dataframe(cluster_stats)
                        
                        uploaded_file = st.file_uploader("Unggah Model (kmeans_model.pkl)", type="pkl")

                        if uploaded_file is not None:
                            # Memuat model dan cluster_stats dari file yang diunggah
                            model, cluster_stats = pickle.load(uploaded_file)

                            st.subheader('Statistik untuk Setiap Klaster')
                            st.dataframe(cluster_stats)
                        # Bagian yang baru ditambahkan untuk menerima data dari pengguna dan melakukan prediksi
                        st.subheader("Prediksi Klaster untuk Sukuk Baru")
                                
                        # Menerima data dari pengguna
                        nama_sukuk = st.text_input('Nama Sukuk:')
                        nilai_nominal = st.number_input('Nilai Nominal (Milyar):', min_value=0.0)
                        interest = st.number_input('Interest/ Disc rate (%):', min_value=0.0)
                        listing = st.date_input('Listing Date:')
                        mature = st.date_input('Mature Date:')

                        if 'df_new' not in st.session_state:
                            st.session_state['df_new'] = pd.DataFrame(columns=['Nama Sukuk', 'Nilai Nominal (Billion Rp)', 'Interest/ Disc rate (%)', 'Listing Date', 'Mature Date'])

                        if st.button("Tambah"):
                            data_baru = pd.DataFrame({'Nama Sukuk': [nama_sukuk], 'Nilai Nominal (Billion Rp)': [ nilai_nominal], 'Interest/ Disc rate (%)': [interest], 'Listing Date': [listing], 'Mature Date':[mature]})
                            if 'df_new' not in st.session_state:
                                st.session_state['df_new'] = data_baru
                            else:
                                st.session_state['df_new'] = pd.concat([st.session_state['df_new'], data_baru], ignore_index=True)
                                
                        st.write("Data yang Ditambahkan:")
                        st.dataframe(st.session_state['df_new'])  # Menampilkan DataFrame setelah pengguna menekan "Tambah"

                        # Ketika pengguna menekan tombol "Prediksi", lakukan prediksi klaster
                        if st.button("Prediksi"):
                            # Menghitung nilai 
                            tanggal_terbaru = pd.Timestamp.now().date()  # Perbarui tanggal saat ini
                            df = st.session_state['df_new']
                            df['Effective Date (Month)'] = ((df['Mature Date'] - df['Listing Date']) / pd.Timedelta(days=30)).astype(int)
                            # Menghapus kolom
                            excludeColumn = ['Listing Date', 'Mature Date']
                            dfSorted = df.drop(excludeColumn, axis=1)

                            st.write(dfSorted)
                            # Melakukan prediksi klaster menggunakan model yang telah dilatih
                            X = dfSorted[['Nilai Nominal (Billion Rp)', 'Interest/ Disc rate (%)', 'Effective Date (Month)']]
                            prediksi_klaster = model.predict(X)
                            
                            # Menambahkan kolom prediksi ke df_RFM
                            df['Klaster'] = prediksi_klaster

                            # Menampilkan DataFrame hasil
                            st.write("Hasil Prediksi:")
                            st.dataframe(df)
                            
                            # Memungkinkan pengguna untuk mengunduh hasil sebagai file CSV
                            csv_download_link(df, 'Hasil_prediksi.csv', 'Unduh Hasil Prediksi')
                            
                    # else:
                    #     st.write("Anda harus mengekspor model sebelum melakukan prediksi.")
            elif Menu == 'Riwayat':
                st.write("## Riwayat Pengolahan Data")

                if 'user_id' not in st.session_state:
                    user_id = get_user_id(username)
                    if user_id:
                        st.session_state['user_id'] = user_id
                    else:
                        st.error("User ID tidak ditemukan")

                if 'user_id' in st.session_state:
                    history = get_history_from_db(st.session_state['user_id'])



                if history:
                    # Menambahkan CSS untuk mempercantik tabel
                    st.markdown("""
                    <style>
                    .custom-table-header {
                        background-color: #f0f0f0;
                        font-weight: bold;
                        text-align: center;
                        padding: 8px;
                        font-size: 20px;
                    }
                    .custom-table-row {
                        text-align: center;
                        padding: 20px;
                        font-size: 20px;
                        margin: 2px;
                    }
                    .custom-table-row-buttons {
                        display: flex;
                        justify-content: space-around;
                        align: center;
                        margin: 0;
                    }
                    .custom-table-row-buttons button {
                        margin: 0 5px;
                        border-bottom: 1px solid #ddd;
                    }
                    .custom-table-row-buttons .download-btn {
                        background-color: #4CAF50;
                        color: white;
                        border-bottom: 1px solid #ddd;
                    }
                    .custom-table-row-buttons .delete-btn {
                        background-color: #f44336;
                        color: white;
                        border-bottom: 1px solid #ddd;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    # Membuat DataFrame dari user_table untuk mempermudah manipulasi data
                    # hasil = pd.DataFrame(data)
                    colms = st.columns((1, 2, 2, 2))
                    fields = ['No', 'Tanggal', 'Dataset', 'Aksi']

                    for col, field_name in zip(colms, fields):
                        col.markdown(f"<div class='custom-table-header'>{field_name}</div>", unsafe_allow_html=True)
                    
                    for idx, record in enumerate(history):
                        col22, col23, col24, col25, col26= st.columns((1, 2, 2, 1, 1))
                        col22.markdown(f"<div class='custom-table-row'>{idx+1}</div>", unsafe_allow_html=True)
                        col23.markdown(f"<div class='custom-table-row'>{record['created_at']}</div>", unsafe_allow_html=True)
                        col24.markdown(f"<div class='custom-table-row'>{record['dataset_name']}</div>", unsafe_allow_html=True)
                        
                        # Kolom untuk tombol unduh
                        with col25:
                            st.markdown(f"<div class='custom-table-row-buttons'>", unsafe_allow_html=True)
                            blob_data = get_blob_data(record['id'])
                            if blob_data:
                                create_download_button(blob_data, f"data_{record['id']}.csv")
                            st.markdown(f"</div>", unsafe_allow_html=True)

                        with col26:
                            st.markdown(f"<div class='custom-table-row-buttons'>", unsafe_allow_html=True)
                            with stylable_container(
                                "red",
                                css_styles=[
                                    """
                                    button {
                                        background-color: #FF0000;
                                        color: white;
                                    }
                                    """,
                                    """
                                    button:hover {
                                        background-color: white;
                                        color: #FF0000;
                                    }
                                    """,
                                ]
                            ):
                                delete_button = st.button(f"Hapus", record['id'])
                            
                            if delete_button:
                                delete_data_from_db(record['id'])  # Lakukan aksi penghapusan data
                                st.success("Data berhasil dihapus.")
                                st.experimental_rerun()
                            st.markdown(f"</div>", unsafe_allow_html=True)

                        # button_phold = col14.empty()

                        # with button_phold.container():
                        #     blob_data = get_blob_data(record['id'])
                        #     if blob_data:
                        #         create_download_button(blob_data, f"data_{record['id']}.csv")
                                

                        #     with stylable_container(
                        #         "red",
                        #         css_styles=["""
                        #             button {
                        #                 background-color: #FF0000;
                        #                 color: white;
                        #             }
                        #             """,
                        #             """
                        #             button:hover {
                        #                 background-color: white;
                        #                 color: #FF0000;
                        #             }
                        #             """,
                        #         ]
                        #     ):
                        #         delete_button = st.button(f"Hapus", record['id'])
                        #     if delete_button:
                        #         # Lakukan beberapa aksi dengan data baris tersebut
                        #         delete_data_from_db(record['id'])  # contoh aksi yang dilakukan
                                
                        #         # Menghapus tombol setelah ditekan
                        #         button_phold.empty()
                        #         st.success("Data berhasil dihapus.")
                        #         st.experimental_rerun()
                    
                else:
                    st.write("Tidak ada data riwayat yang tersedia.")


            elif Menu == 'Profil':
                if "username" in st.session_state and st.session_state["username"]:
                    profile_page(st.session_state["username"])
    
if __name__ == "__main__":
    main()

    