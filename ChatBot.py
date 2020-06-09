#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import telegram
import requests
import re
import sqlite3
from telegram.error import NetworkError, Unauthorized
from time import sleep
from sqlite3 import Error
from datetime import date
update_id = None
comando_ocupado = False
url = "https://www.etnassoft.com/api/v1/get/"

def main():
    global update_id
    bot = telegram.Bot('1124147371:AAEU-1unIWr0Zc1JEnubJlqFPgBBZSEBDw0')
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            update_id += 1
            

def echo(bot):
    global update_id
    global comando_ocupado
    global url
    conexion = sql_conexion();
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        chat_id = str(update.message.chat.id)
        nick = str(update.message.chat.username)
        nombre = str(update.message.chat.first_name)
        apellidos = str(update.message.chat.last_name)
        fecha_actual = str(obtener_fechaactual())
        
        if(buscar_usuario(conexion,str(chat_id))==0):
            insertar_usuario(conexion,chat_id,nick,nombre,apellidos)
            insertar_acceso(conexion,chat_id,fecha_actual)
        else:
            if(buscar_acceso(conexion,chat_id,fecha_actual) == 0):
                insertar_acceso(conexion,chat_id,fecha_actual)
            else:
                actualizar_acceso(conexion,chat_id,fecha_actual)
                
        if update.message:
            opcion = update.message.text
            if(comando_ocupado):
                if(comando_ocupado == 2):
                    enviar_mensaje(update,"Espere un momento por favor, estamos procesando su solicitud...")
                    libros = obtener_libros(url + "?keyword=" + opcion)
                    if(libros):
                        for libro in libros:
                            if(buscar_libro(conexion,libro['ID'])==0):
                                insertar_libro(conexion,libro['ID'],str(libro['title']),str(libro['author']))
                            else:
                                actualizar_libro(conexion,libro['ID'])
                            if(buscar_usuario_libro(conexion,chat_id,libro['ID'])==0):
                                insertar_usuario_libro(conexion,chat_id,libro['ID'])
                            else:
                                actualizar_usuario_libro(conexion,chat_id,libro['ID'])
                                
                            enviar_mensaje(update,"ID: "+libro['ID']+"\nTítulo: "+libro['title']+"\nAutor: "+libro['author']+"\nIdioma: "+libro['language'])
                    else:
                        enviar_mensaje(update,"Lo sentimos, no encontramos ningún resultado.")
                elif(comando_ocupado == 3):
                    enviar_mensaje(update,"Espere un momento por favor, estamos procesando su solicitud...")
                    libros = obtener_libros(url + "?id=" + opcion)
                    if(libros):
                        for libro in libros:
                            if(buscar_libro(conexion,libro['ID'])==0):
                                insertar_libro(conexion,libro['ID'],str(libro['title']),str(libro['author']))
                            else:
                                actualizar_libro(conexion,libro['ID'])
                            if(buscar_usuario_libro(conexion,chat_id,libro['ID'])==0):
                                insertar_usuario_libro(conexion,chat_id,libro['ID'])
                            else:
                                actualizar_usuario_libro(conexion,chat_id,libro['ID'])    
                                
                            contenido = limpiar_html(libro['content']) 
                            enviar_imagen(libro['cover'],bot,update)
                            enviar_mensaje(update,"ID: "+libro['ID']+"\nTítulo: "+libro['title']+"\nAutor: "+libro['author']+"\nIdioma: "+libro['language']+"\nContenido:\n"+contenido)
                    else:
                        enviar_mensaje(update,"Lo sentimos, no encontramos ningún resultado.")
                elif(comando_ocupado == 4):
                    enviar_mensaje(update,"Espere un momento por favor, estamos procesando su solicitud...")
                    libros = obtener_libros(url + "?id=" + opcion)
                    if(libros):
                        for libro in libros:
                            if(buscar_libro(conexion,libro['ID'])==0):
                                insertar_libro(conexion,libro['ID'],str(libro['title']),str(libro['author']))
                            else:
                                actualizar_libro(conexion,libro['ID'])
                            if(buscar_usuario_libro(conexion,chat_id,libro['ID'])==0):
                                insertar_usuario_libro(conexion,chat_id,libro['ID'])
                            else:
                                actualizar_usuario_libro(conexion,chat_id,libro['ID'])
                            
                            descarga = libro['url_download']
                            enviar_archivo(descarga,bot,update)
                comando_ocupado = False
            else:
                if(opcion=="/recomendar_libros"):
                    comando_ocupado = 1
                    enviar_mensaje(update,"Espere un momento por favor, estamos procesando su solicitud...")
                    libros = obtener_libros(url + "?criteria=most_viewed")
                    for libro in libros:
                        if(buscar_libro(conexion,libro['ID'])==0):
                            insertar_libro(conexion,libro['ID'],str(libro['title']),str(libro['author']))
                        else:
                            actualizar_libro(conexion,libro['ID'])
                        if(buscar_usuario_libro(conexion,chat_id,libro['ID'])==0):
                            insertar_usuario_libro(conexion,chat_id,libro['ID'])
                        else:
                            actualizar_usuario_libro(conexion,chat_id,libro['ID'])
                            
                        enviar_mensaje(update,"ID: "+libro['ID']+"\nTítulo: "+libro['title']+"\nAutor: "+libro['author']+"\nIdioma: "+libro['language'])
                    comando_ocupado = False
                elif(opcion=="/buscar_libros_por_tag"):
                    comando_ocupado = 2
                    enviar_mensaje(update,"Por favor ingrese un tag o etiqueta a buscar.\nEjemplo: programación")
                elif(opcion=="/mostrar_libro"):
                    comando_ocupado = 3
                    enviar_mensaje(update,"Por favor ingrese el código del libro a mostrar.\nEjemplo: 9004")
                elif(opcion=="/descargar_libro"):
                    comando_ocupado = 4
                    enviar_mensaje(update,"Por favor ingrese el código del libro a descargar.\nEjemplo: 9004")
                else:
                    enviar_mensaje(update,"No ha elegido una opción correcta\nPruebe con alguna de las siguientes:\n/recomendar_libros\n/buscar_libros_por_tag\n/mostrar_libro\n/descargar_libro")
                    comando_ocupado = False
#Funciones importantes#
def obtener_libros(url):
    response = requests.get(url)
    if response.status_code == 200:
        libros = response.json()
        return libros
    else:
        return False
    
def limpiar_html(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  cleantext = cleantext.replace("&lt;li&gt;","").replace("&lt;ul&gt;","").replace("&lt;/ul&gt;","").replace("&lt;/li&gt;","")
  cleantext = cleantext.replace("&aacute;","á").replace("&eacute;","é").replace("&iacute;","í").replace("&oacute;","ó").replace("&uacute;","ú")
  cleantext = cleantext.replace("&Aacute;","Á").replace("&Eacute;","É").replace("&Iacute;","Í").replace("&Oacute;","Ó").replace("&Uacute;","Ú")
  cleantext = cleantext.replace("&ntilde;","ñ").replace("&Ntilde;","Ñ").replace("&nbsp;"," ").replace("&ldquo;",'"').replace("&rdquo;",'"')
  cleantext = cleantext.replace("&iquest;","¿").replace("&quot;",'"').replace('&lt;a href="',"").replace("&lt;/a&gt;","").replace('&lt;',"").replace('&gt;',"")
  cleantext = cleantext.replace("&raquo;",">").replace("&laquo;","<").replace("&#039;","'")
  return cleantext

def enviar_mensaje(update,mensaje):
    update.message.reply_text(mensaje)
    
def enviar_imagen(url, bot, update):
    nombrelocal = 'imagen.jpg'
    imagen = requests.get(url).content
    with open(nombrelocal,"wb") as handler:
        handler.write(imagen)
    with open(nombrelocal,"rb") as photo_file:
        bot.sendPhoto(chat_id=update.message.chat.id,photo=photo_file);

def enviar_archivo(url,bot,update):
    enviar_mensaje(update,"Link de descarga:\n" + url)


def sql_conexion():
    try:
        con = sqlite3.connect('recomendador_libros.db')
        return con
    except Error:
        print(Error)    
        
def buscar_usuario(con, id_chat):
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * FROM usuario WHERE id_chat='"+id_chat+"'")
    rows = cursorObj.fetchall()
    if rows :
        return rows
    return 0

def insertar_usuario(con, id_chat,nick,nombre,apellidos):
    cursorObj = con.cursor()
    cursorObj.execute("INSERT INTO usuario VALUES('"+id_chat+"','"+nick+"','"+nombre+"','"+apellidos+"')")
    con.commit()
    
def buscar_acceso(con,id_chat,fecha_actual):
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * FROM acceso WHERE id_chat='"+id_chat+"' AND fecha='"+fecha_actual+"'")
    rows = cursorObj.fetchall()
    if rows :
        return rows
    return 0

def actualizar_acceso(con,id_chat,fecha_actual):
    cursorObj = con.cursor()
    cursorObj.execute("UPDATE acceso SET num_usos = num_usos + 1 WHERE id_chat='"+id_chat+"' AND fecha='"+fecha_actual+"'")
    con.commit()
    
def insertar_acceso(con, id_chat,fecha):
    cursorObj = con.cursor()
    cursorObj.execute("INSERT INTO acceso VALUES('"+id_chat+"','"+fecha+"',0)")
    con.commit()
    
def obtener_fechaactual():
    today = date.today();
    hoy = "{}".format(today.day)+"/{}".format(today.month)+"/{}".format(today.year)
    return hoy

def buscar_libro(con,id_libro):
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * FROM libros_buscados WHERE id_libro="+id_libro)
    rows = cursorObj.fetchall()
    if rows :
        return rows
    return 0

def insertar_libro(con, id_libro,titulo,autor):
    cursorObj = con.cursor()
    cursorObj.execute("INSERT INTO libros_buscados VALUES("+id_libro+",'"+titulo+"','"+autor+"',1)")
    con.commit()

def actualizar_libro(con, id_libro):
    cursorObj = con.cursor()
    cursorObj.execute("UPDATE libros_buscados SET num_busq = num_busq + 1 WHERE id_libro="+id_libro)
    con.commit()

def buscar_usuario_libro(con, id_chat, id_libro):
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * FROM usuario_libro WHERE id_libro="+id_libro+" AND id_chat='"+id_chat+"'")
    rows = cursorObj.fetchall()
    if rows :
        return rows
    return 0
def insertar_usuario_libro(con, id_chat, id_libro):
    cursorObj = con.cursor()
    cursorObj.execute("INSERT INTO usuario_libro VALUES('"+id_chat+"',"+id_libro+",1)")
    con.commit()
    
def actualizar_usuario_libro(con, id_chat, id_libro):
    cursorObj = con.cursor()
    cursorObj.execute("UPDATE usuario_libro SET num_acce = num_acce + 1 WHERE id_libro="+id_libro+" AND id_chat='"+id_chat+"'")
    con.commit()
    
if __name__ == '__main__':
    main()