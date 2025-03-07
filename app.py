from flask import Flask, request,abort, jsonify
import requests
import json

#app = Flask("monday-server")
app = Flask(__name__)

# Configuración de APIs
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQzNTUzODI2NCwiYWFpIjoxMSwidWlkIjo1NTA0OTQ4NywiaWFkIjoiMjAyNC0xMS0xMlQxMzo0NzoyNS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjA5ODM5NTMsInJnbiI6InVzZTEifQ.R0agHiyUGpEhWbCFvEWt7w_5yCsMZVYu0mi8YAHqHag"
MONDAY_URL = "https://api.monday.com/v2"
EXTERNAL_API_URL = "https://test-apiwarden.portalns.es/api/monday/citasPaciente"
#Id del tablero IP (IPs-test='8079345425') (IPs Pre-approval='6575767453')
MONDAY_BOARD_ID = "6575767453";
#Id del tablero citasPaciente
CITAS_BOARD_ID = "8078247682";
#Id del tablero manejo reservas de banco
CRIOBANCO_BOARD_ID = "7201636037";
NHPaciente = '';
CodIpPaciente = '';
NombrePaciente = '';
NumeroDocumento = '';

#1- metodo para obtener el Codigo Ip desde Monday
def get_codip_from_monday(item_id): 
    print(f"Entrando a obtener el CodIP para el item: {item_id},")
    #Obtiene el valor de 'CodIP' desde un tablero de Monday.com. , item_id representa el id del elemento 
    #Item dentro del tablero recibido desde el pulse del webhook
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    #consulta GraphQL para obtener las columnas del Item mediante el item_recibido en el pulso
    query = {
        "query": f'''
        query {{
            items(ids:[ {item_id}]) {{
                id, name,
                column_values {{
                    id
                    text
                }}
            }}
        }}
        '''
    }

    response = requests.post(MONDAY_URL, headers=headers, json=query)

    if response.status_code == 200:
        data = response.json()
        item_data = data["data"]["items"][0]
        item_info = {
            "CodIP": None,
            "NombrePaciente": item_data["name"]  # Obtener el valor del Name del item
        }
        #(MAPEO EN IPs Pre-approval)
        for column in item_data["column_values"]:
            if column["id"] == "codigo_ip__1": 
                item_info["CodIP"] = column["text"]
            if column["id"] == "nh":#Esta columna no existe en este tablero 
                item_info["NHPaciente"] = column["text"]
                #print(f"El NH es:"+ NHPaciente)
            if column["id"] == "texto__1": 
                item_info["NumeroDocumento"] = column["text"]                
        return item_info           
        #(MAPEO EN IPs-test)
        #for column in item_data["column_values"]:
            #if column["id"] == "codigo_ip__1": 
                #item_info["CodIP"] = column["text"]
            #if column["id"] == "texto_mkkbaxzb": 
                #item_info["NHPaciente"] = column["text"]
                #print(f"El NH es:"+ NHPaciente)
            #if column["id"] == "texto__1": 
                #item_info["NumeroDocumento"] = column["text"]                
        #return item_info 
    else:
        print(f"Error al consultar Monday: {response.status_code}")
        return None

#2- Consultar citas paciente
def get_citas_paciente(CodIP):
    print(f"Entrando en get_citas_paciente")
    #Consulta citas paciente con el valor de 'CodIP'.
    try:
        # URL del API externo
        external_api_url = "https://test-apiwarden.portalns.es/api/monday/citasPaciente"

        # Parámetros y autenticación
        params = {'nh': CodIP}
        auth = ('novafem', 'monday')  # Username y Password

        # Realizar la solicitud GET con autenticación
        response = requests.get(external_api_url, params=params, auth=auth)

        # Manejo de errores en la respuesta
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al consultar el API externo: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectarse al API externo: {e}")
        return None

#3- Consultar muestras paciente
def get_muestras_paciente(CodIP):
    print(f"Entrando en get_muestras_paciente")
    #Consulta muestras de banco del paciente con el valor de 'CodIP'.
    try:
        # URL del API externo
        external_api_url = "https://test-apiwarden.portalns.es/api/monday/muestrasPaciente"

        # Parámetros y autenticación
        params = {'nh': CodIP}
        auth = ('novafem', 'monday')  # Username y Password

        # Realizar la solicitud GET con autenticación
        response = requests.get(external_api_url, params=params, auth=auth)

        # Manejo de errores en la respuesta
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al consultar el API externo: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectarse al API externo: {e}")
        return None        

#4- validar si existe o no el elemento (devuelve boolean)
def cita_exists_in_monday(item_name):    
    print(f"Validando si Cita existe--> item_name:{item_name}")
    # Verifica si un item con el mismo ID de cita ya existe en el tablero (sin límite de 100)
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    items = []
    cursor = None
    
    while True:
        query = {
            "query": f'''
            query {{
                boards(ids: {CITAS_BOARD_ID}) {{
                    items_page(limit: 100, cursor: {json.dumps(cursor) if cursor else "null"}) {{
                        cursor
                        items {{
                            id
                            name
                        }}
                    }}
                }}
            }}
            '''
        }
        response = requests.post(MONDAY_URL, headers=headers, json=query)
        
        if response.status_code == 200:
            data = response.json()
            items.extend(data["data"]["boards"][0]["items_page"]["items"])
            cursor = data["data"]["boards"][0]["items_page"].get("cursor")
            if not cursor:
                break  # No hay más páginas, terminamos
        else:
            return False  # Error en la consulta, asumimos que no existe
    
    return any(item["name"] == item_name for item in items)

def muestra_exists_in_monday(item_name):    
    print(f"Validando si Muestra existe--> item_name:{item_name}")
    # Verifica si un item con el mismo ID de cita ya existe en el tablero (sin límite de 100)
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    items = []
    cursor = None
    
    while True:
        query = {
            "query": f'''
            query {{
                boards(ids: {CRIOBANCO_BOARD_ID}) {{
                    items_page(limit: 100, cursor: {json.dumps(cursor) if cursor else "null"}) {{
                        cursor
                        items {{
                            id
                            name
                        }}
                    }}
                }}
            }}
            '''
        }
        response = requests.post(MONDAY_URL, headers=headers, json=query)
        
        if response.status_code == 200:
            data = response.json()
            items.extend(data["data"]["boards"][0]["items_page"]["items"])
            cursor = data["data"]["boards"][0]["items_page"].get("cursor")
            if not cursor:
                break  # No hay más páginas, terminamos
        else:
            return False  # Error en la consulta, asumimos que no existe
    
    return any(item["name"] == item_name for item in items)

#5- Si no existe crear el item en el tablero de CitasPaciente
def create_item_cita(item_data, CodIP, NombrePaciente):
    print(f"Entrando en create_item_cita")
    # Crea un item en Monday.com solo si no existe
    if cita_exists_in_monday(str(item_data.get("id", ""))):
        print(f"El item {item_data.get('id')} ya existe en Monday.com, no se creará nuevamente.")
        return
        
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    column_values = {
        "texto_mkkbk719": str(item_data.get("id", "")),#ID
        "n_meros_mkkb482d": item_data.get("profesionales", ""),#profesionales
        "texto_mkkbnye0": item_data.get("profesionales.name", ""),#texto_profesional
        "n_meros_mkkbjd7b": item_data.get("historias", 0),#numero_historias
        "n_meros_mkkb5dwx": item_data.get("citas_concep.id", ""),#Citas_concep.id
        "texto_mkkbr2jc": item_data.get("citas_concep.name", ""),#concepto_cita
        "texto_mkkb9txq": item_data.get("fecha", "").split("T")[0],#fecha_cita
        "texto_mkkbd68h": item_data.get("hora", ""),#hora_cita
        "texto_mkkbhz9d": item_data.get("estados_citas", ""),#estados_citas
        "texto_mkkbqmst": item_data.get("estados_citas.name", ""),#estados_citas.name
        "text_mkntb8xy": item_data.get("historias.tlf1", ""),#Teléfono
        "texto_mkkbc2cz": CodIP,
        "texto_mkkbsc4y": NombrePaciente
    }
    backslash_char = "\\"
    columnValues = json.dumps(column_values).replace('"', '\\"')
    #column_values: "{json.dumps(column_values).replace('"', '\\"')}"
    
    #Mutacion para realizar la operacion de creacion de items en el tablero especificad
    query = {
        "query": f'''
        mutation {{
            create_item(
                board_id: {CITAS_BOARD_ID},
                item_name: "{item_data["id"]}",
                column_values: "{columnValues}"
            ) {{
                id
            }}
        }}
        '''
    }

    response = requests.post(MONDAY_URL, headers=headers, json=query)
    if response.status_code == 200:
        print(f"Item creado en Monday.com: {response.json()}")
    else:
        print(f"Error al crear el item en Monday.com: {response.status_code}")
        print(response.text)
        
#6- Si no existe crear el item en el tablero de CrioBanco
def create_item_criobanco(item_data, CodIP, NombrePaciente, NumeroDocumento):
    print(f"Entrando en create_item_criobanco")
    # Crea un item en Monday.com solo si no existe
    if muestra_exists_in_monday(str(item_data.get("id", ""))):
        print(f"El item {item_data.get('id')} ya existe en CrioBanco, no se creará nuevamente.")
        return
        
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    column_values = {
        #"": str(item_data.get("id", "")),#ID - No hay columna Id en este tablero
        #"": item_data.get("historias", ""),#historias
        #"": item_data.get("eda_his", ""),#eda_his
        "date_mknr2s60": item_data.get("fec_entra", "").split("T")[0],#fec_entra --> Fecha Entrada
        #"": item_data.get("hor_ent", ""),#hor_ent
        "date_mknravmw": item_data.get("fec_salida", "").split("T")[0],#fec_salida --> Fecha Salida
        "text_mknrqbv4": item_data.get("destino.name", ""),#destino.name
        "text_mknrwgre": item_data.get("destino", ""),#destino
        "n_meros__1": item_data.get("numero_embrion", 0),#numero_embrion --> Cantidad total de Óvulos
        "text_mknrm2kr": item_data.get("emb_dia", ""),#emb_dia
        "text_mknr956h": item_data.get("emb_dia.name", ""),#emb_dia.name
        #"": item_data.get("tp", ""),#tp
        "color_mknr3xrk": item_data.get("tp.name", ""),#tp.name --> Tipo Gameto
        "numeric_mkns66z3": NumeroDocumento,#Número de documento 
        "text_mkns6kpb": NombrePaciente #Ip
    }

    columnValues = json.dumps(column_values).replace('"', '\\"')
    
    #Mutacion para realizar la operacion de creacion de items en el tablero especificad
    query = {
        "query": f'''
        mutation {{
            create_item(
                board_id: {CRIOBANCO_BOARD_ID},
                item_name: "{item_data["id"]}",
                column_values: "{columnValues}"
            ) {{
                id
            }}
        }}
        '''
    }

    response = requests.post(MONDAY_URL, headers=headers, json=query)
    if response.status_code == 200:
        print(f"Item criobanco creado en Monday.com: {response.json()}")
    else:
        print(f"Error al crear el item criobanco en Monday.com: {response.status_code}")
        print(response.text)
    
#7- actualizar el estado del campo ObtenerDatosVrpro
def update_item_status(item_id):
    # Actualiza la columna 'estado_1_mkkbqk95' a "Finalizado"
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    #column_values = json.dumps({"estado_1_mkkbqk95": {"label": "Finalizado"}}).replace('"', '\\"')
    query = {
        "query": f'''
        mutation {{
            change_column_value(
                board_id: {MONDAY_BOARD_ID},
                item_id: {item_id},
                column_id: "estado_1_mkkbqk95",
                value: "{{\\"label\\": \\\"Finalizado\\"}}"
            ) {{
                id
            }}
        }}
        '''
    }
    response = requests.post(MONDAY_URL, headers=headers, json=query)
    if response.status_code == 200:
        print(f"Estado del item {item_id} actualizado a 'Finalizado'.")
    else:
        print(f"Error al actualizar el estado del item: {response.status_code}")

#8- notificarle al usuario la finalizacion de la integracion
def send_notification_to_user(user_id, message):
    # Envía una notificación a un usuario en Monday.com
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    query = {
        "query": f'''
        mutation {{
            create_notification(
                user_id: {user_id},
                target_id: {MONDAY_BOARD_ID},
                target_type: Project,
                text: "{message}"
            ) {{
                text
            }}
        }}
        '''
    }
    response = requests.post(MONDAY_URL, headers=headers, json=query)
    if response.status_code == 200:
        print(f"Notificación enviada a usuario {user_id}.")
    else:
        print(f"Error al enviar notificación: {response.status_code}")

#Metodo para escuchar el webHook, gestionar el challenge y procesar el pulso recibido a traves del servicio
@app.route("/webhook", methods=["POST"])
def webhook_handler():
    #Maneja el webhook enviado por Monday.com.
    data = request.json

    #validar si es el challenge o un pulso
    if "challenge" in data:
        if request.method == 'POST':
            #data = request.get_json()
            challenge = data['challenge']            
            return jsonify({'challenge': challenge})
            # print(request.json)
            # return 'success', 200
        else:
            abort(400)
    else:            
        item_id = data.get("event", {}).get("pulseId")  # ID del elemento
        board_id = data.get("event", {}).get("boardId")  # ID del tablero
        user_id = data.get("event", {}).get("userId")
        mensaje = ""

        if not item_id or not board_id or not user_id:
            mensaje = "ERROR: No se proporcionaron IDs válidos"
            return jsonify({"error": "No se proporcionaron IDs válidos"}), 400

        print(f"Webhook recibido: Item ID: {item_id}, Board ID: {board_id}, User ID: {user_id}")

        # 1) Obtener el valor de Codigo IP desde Monday
        item_info = get_codip_from_monday(item_id)
        if not item_info or not item_info["CodIP"]:
            mensaje = "ERROR: No se pudo obtener el CodIP"
            return jsonify({"error": "No se pudo obtener el CodIP"}), 400
        
        CodIP = item_info["CodIP"]
        NombrePaciente = item_info["NombrePaciente"]
        #NHPaciente = item_info["NHPaciente"]
        NumeroDocumento = item_info["NumeroDocumento"]
        print(f"Se obtuvo...CodIP: {CodIP} ,NombrePaciente: {NombrePaciente} ,NHPaciente:{NHPaciente} , NumeroDocumento {NumeroDocumento}")
        mensaje = f"Completado con éxito, se han obtenido los datos para IP : {NombrePaciente}"
        # 2) Una vez identificado el CodIP se obtienen los datos que necesitan ser enviados hacia Monday.com
        # Consultar citas paciente
        # citas_paciente = get_citas_paciente(NHPaciente)
        citas_paciente = get_citas_paciente(CodIP)
        if not citas_paciente:
            mensaje = f"ERROR: No se obtuvieron citas para IP : {NombrePaciente}"
            return jsonify({"error": "No se obtuvieron citas del paciente"}), 400
        # Consultar muestras paciente
        # muestras_paciente = get_muestras_paciente(NHPaciente)
        muestras_paciente = get_muestras_paciente(CodIP)
        if not muestras_paciente:
            mensaje = "ERROR: No se obtuvieron muestras de banco para IP : {NombrePaciente}"
            return jsonify({"error": "No se obtuvieron muestras del paciente"}), 400            

        # 3) Una vez obtenido los datos desde el API o BD
        # Por cada elemento recibido de Citas paciente, se debe validar si existe o no el elemento
        # Si no existe crear el item en el tablero de CitasPaciente
        for item in citas_paciente:
            create_item_cita(item, CodIP, NombrePaciente)

        # Por cada elemento recibido de Muestras paciente, se debe validar si existe o no el elemento
        # Si no existe crear el item en el tablero de CrioBanco
        for item in muestras_paciente:
            create_item_criobanco(item, CodIP, NombrePaciente, NumeroDocumento)

        # 4) Actualizar el estado de la transaccion a Finalizado
        update_item_status(item_id)  # Actualiza el estado del item a "Finalizado"
        
        # 5) Notificar la notificacion de finalizacion de  la transaccion
        send_notification_to_user(user_id, f"Integración VRPRO: {mensaje}")

        print(f"Integración completada con exito")
        return jsonify({"message": "Integración completada con éxito"}), 200

if __name__ == "__main__":
    app.run(port=3690, debug=True)