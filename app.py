from flask import Flask, request, jsonify
import requests
import json

#app = Flask("monday-server")
app = Flask(__name__)

# Configuración de APIs
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQzNTUzODI2NCwiYWFpIjoxMSwidWlkIjo1NTA0OTQ4NywiaWFkIjoiMjAyNC0xMS0xMlQxMzo0NzoyNS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjA5ODM5NTMsInJnbiI6InVzZTEifQ.R0agHiyUGpEhWbCFvEWt7w_5yCsMZVYu0mi8YAHqHag"
MONDAY_URL = "https://api.monday.com/v2"
EXTERNAL_API_URL = "https://test-apiwarden.portalns.es/api/monday/citasPaciente"
#Id del tablero IPs-test
MONDAY_BOARD_ID = "8079345425";
#Id del tablero citasPaciente
CITAS_BOARD_ID = "8078247682";
NHPaciente = '';
NombrePaciente = '';

def get_nh_from_monday(item_id): 
    print(f"Entrando a obtener el nh para el item: {item_id},")
    #Obtiene el valor de 'nh' desde un tablero de Monday.com. , item_id representa el id del elemento 
    #Item dentro del tablero recibido desde el pulse del webhook
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    query = {
        "query": f'''
        query {{
            items(ids:[ {item_id}]) {{
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
        # Busca el valor del parámetro 'nh' en las columnas del elemento
        for column in data["data"]["items"][0]["column_values"]:
            #if column["id"] == "texto_mkkbaxzb": #Reemplaza 'nh' por el ID real de la columna ---> texto_mkkbaxzb
            if column["id"] == "texto_mkkbaxzb":  # Reemplaza 'nh' por el ID real de la columna ---> texto_mkkbaxzb
                NHPaciente = column["text"]
                print(f"El NH es:"+ NHPaciente)
                return column["text"]
        return None
    else:
        print(f"Error al consultar Monday: {response.status_code}")
        return None

def get_external_data(nh):
    #Consulta el API externo con el valor de 'nh'.
    try:
        # URL del API externo
        external_api_url = "https://test-apiwarden.portalns.es/api/monday/citasPaciente"

        # Parámetros y autenticación
        params = {'nh': nh}
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

def create_item_in_monday(item_data, nh):
    #Crea un elemento (item) en un tablero de Monday.com.
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
        "texto_mkkbc2cz": nh
        #"texto_mkkbsc4y": NombrePaciente #NombrePaciente
    }
    backslash_char = "\\"
    columnValues = json.dumps(column_values).replace('"', '\\"')
    #column_values: "{json.dumps(column_values).replace('"', '\\"')}"
    
    query = {
        "query": f'''
        mutation {{
            create_item(
                board_id: {CITAS_BOARD_ID},
                item_name: "Cita ID: {item_data["id"]}",
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

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    #Maneja el webhook enviado por Monday.com.
    data = request.json
    item_id = data.get("event", {}).get("pulseId")  # ID del elemento
    board_id = data.get("event", {}).get("boardId")  # ID del tablero

    if not item_id or not board_id:
        return jsonify({"error": "No se proporcionaron IDs válidos"}), 400

    print(f"Webhook recibido: Item ID: {item_id}, Board ID: {board_id}")

    # Obtener el valor de nh desde Monday
    nh = get_nh_from_monday(item_id)
    if not nh:
        return jsonify({"error": "No se pudo obtener el valor de nh"}), 400

    # Consultar el API externo
    external_data = get_external_data(nh)
    if not external_data:
        return jsonify({"error": "No se obtuvieron datos del API externo"}), 400

    # Crear items en el tablero con los datos obtenidos
    for item in external_data:
        create_item_in_monday(item, nh)

    return jsonify({"message": "Integración completada con éxito"}), 200

if __name__ == "__main__":
    app.run(port=3690, debug=True)
