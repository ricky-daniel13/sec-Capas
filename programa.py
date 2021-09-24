import sqlite3
import re
from sqlite3 import Error
import face_recognition
import cv2
import numpy as np
import os
import warnings
import time
from cryptography.fernet import Fernet
warnings.filterwarnings("ignore")

#   Variables
cur_direc = os.getcwd()
path = os.path.join(cur_direc, 'caras', "")
key = "2U-gA4xBgTEKQNYs3JogMPfJYq5xNa5PqMaoXWS29uw="

# Objetos
fernet = Fernet(key.encode())


# Metodos
def screen_clear():
    # print("\n\n")
    # return
    # for mac and linux(here, os.name is 'posix')
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        # for windows platfrom
        _ = os.system('cls')

def esUsuario(usuario):
    if re.match("^[a-zA-Z0-9_-]+$", usuario):
        return True
    else:
        return False

def conectar():

    try:

        con = sqlite3.connect('mydatabase.db')

        cursorObj = con.cursor()

        cursorObj.execute('CREATE TABLE IF NOT EXISTS usuarios(id integer PRIMARY KEY, nombre text, contra text, info text)')

        con.commit()

        return con

    except Error:

        print(Error)

def existeUsuario(con, nombre):

    cursorObj = con.cursor()

    cursorObj.execute('SELECT nombre FROM usuarios WHERE nombre = ?', [nombre])

    rows = cursorObj.fetchall()

    cursorObj.close()

    if(len (rows)>0):
        return True
    else:
        return False

def obtenerUsuario(con, nombre):

    cursorObj = con.cursor()

    cursorObj.execute('SELECT id, nombre, info FROM usuarios WHERE nombre = ?', [nombre])

    rows = cursorObj.fetchall()

    cursorObj.close()

    return rows[0]



def nuevoUsario(con, nombre, info, contra):
    cursorObj = con.cursor()

    datos = (nombre, info, (fernet.encrypt(contra.encode()).decode()))

    # print("encoded pass= " + (fernet.encrypt(contra.encode()).decode()))
    cursorObj.execute('INSERT INTO usuarios(nombre, info, contra) VALUES(?, ?, ?)', datos)

    cursorObj.close()

    con.commit()

def tomarFoto(nombre):
    face_locations = []
    process_this_frame = True
    video_capture = cv2.VideoCapture(0)
    while True:
        ret, frame = video_capture.read()
        cleanframe = frame.copy()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        if process_this_frame:
            face_locations = face_recognition.face_locations( rgb_small_frame)
        process_this_frame = not process_this_frame
    # Display the results
        for (top, right, bottom, left) in face_locations:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
    # Draw a rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    # Display the resulting image
        cv2.imshow('Video', frame)
    # Hit 'q' on the keyboard to quit!
        if (cv2.waitKey(1) & 0xFF == ord(' ')) and (len(face_locations)>0) and (len(face_locations)<2):
            cv2.destroyAllWindows()
            cv2.imwrite(os.path.join(path, nombre+".jpg"), cleanframe)
            break

def validarFoto(nombre):
    face_locations = []
    process_this_frame = True

    user_image = face_recognition.load_image_file(os.path.join(path, nombre+".jpg"))
    user_face_encoding = face_recognition.face_encodings(user_image)[0]

    video_capture = cv2.VideoCapture(0)
    while True:
        ret, frame = video_capture.read()
        cleanframe = frame.copy()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        if process_this_frame:
            face_locations = face_recognition.face_locations( rgb_small_frame)
            if (len(face_locations)>0) and (len(face_locations)<2):
                face_encodings = face_recognition.face_encodings( rgb_small_frame, face_locations)
                matches = face_recognition.compare_faces ([user_face_encoding], face_encodings[0])
                if(matches[0]):
                    return True
        process_this_frame = not process_this_frame
    # Display the results
        for (top, right, bottom, left) in face_locations:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
    # Draw a rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    # Display the resulting image
        cv2.imshow('Video', frame)
    # Hit 'q' on the keyboard to quit!
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            cv2.destroyAllWindows()
            return False

def confContra(con, user, contra):

    cursorObj = con.cursor()

    cursorObj.execute('SELECT contra FROM usuarios WHERE nombre = ?', [user])

    rows = cursorObj.fetchall()

    cursorObj.close()
    # encContra = (fernet.encrypt(contra.encode())).decode()
    # print("Contra: " + encContra + " guardadada: " + rows[0][0])

    if(len (rows)>0):
        if fernet.decrypt(rows[0][0].encode()).decode()==contra:
            return True
        else:
            return False
    else:
        return False


def validarUsuario(user, db):
    screen_clear()
    contra = input("Digite su contraseña (Solo letras, numeros, y guiones)\n")
    if (confContra(db, user, contra)):
        print("Confirmando rostro. Presione \"q\" para cancelar")
        if validarFoto(user):
            datos = obtenerUsuario(db, user)
            return datos
        else:
            print("Rostro sin confirmar")
            return False
    else:
        print("Contraseña sin confirmar")
        return False

def menuUsuario(userData, db):
    screen_clear()
    lastOp= time.time()
    validated=True
    usrOpc=1
    while (validated & (usrOpc != 0)):
        screen_clear()
        usrOpc=int(input("Seleccione una opcion\n\t1)Ver datos\n\t0)Salir\n\n"))
        # print(usrOpc)
        timeNow = time.time()
        if ((timeNow-lastOp)<60):
            lastOp=timeNow
            if usrOpc==1:
                print("ID: " + str(userData[0]) + "\nNombre: " + userData[1] + "\nInformacion privada: " + userData[2])
            elif usrOpc==0:
                print("Cerrando sesion")
            input("\n\nPresione Enter para continuar")
        else:
            input("\n\nSeccion invalidada por inactividad. Confirme su identidad.\nPresione enter para continuar")
            if validarUsuario(userData[1], db):
                validated = True
                lastOp= timeNow
            else:
                validated = False
                print("\n\nIdentidad no confirmada, cerrando sesion")
    screen_clear()     
    input("\n\nSeccion cerrada. Presione enter.")

        

# Inicio programa
opc = "E"

db = conectar()

screen_clear()

while(opc!="Y" and opc!="N"):
    opc=input("Crear nueva cuenta? (Y: Si/N: No)\n")

if(opc=="Y"):
    user = input("Escribe un nombre de usuario (Solo letras, numeros, y guiones)\n")
    isNew = False
    while(not isNew):
        while(not esUsuario(user)):
            user = input("Usuario invalido, escribe uno nuevo (Solo letras, numeros, y guiones)\n")
        isNew = not existeUsuario(db, user)
        if(not isNew):
            user = input("Nombre de usuario ya en uso, escribe uno nuevo\n")

    contra = input("Escribe una contraseña (Solo letras, numeros, y guiones)\n")
    while(not esUsuario(contra)):
        contra = input("Contraseña invalida, escribe una nueva (Solo letras, numeros, y guiones)\n")

    info = input("Escribe tu informacion privada\n")
    screen_clear()
    print("Tomando rostro. Cuando su rostro este marcado con un cuadro, presione \"espacio\"")
    tomarFoto(user)
    nuevoUsario(db, user, info, contra)

screen_clear()
print("Inicio de Sesion")
user = input("Digita tu nombre de usuario\n")
while(not esUsuario(user)):
    user = input("Usuario invalido(Solo letras, numeros, y guiones)\n")

if(existeUsuario(db, user)):
    datos = validarUsuario(user, db)
    if(datos):
        menuUsuario(datos, db)

        
    





# sql_insert(con, entities)

