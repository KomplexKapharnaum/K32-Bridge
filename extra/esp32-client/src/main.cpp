#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArtnetWifi.h>


WiFiClient espClient;
PubSubClient client(espClient);

ArtnetWifi artnet;

bool wifiOK = false;
long lastMsg = 0;
char msg[50];
int value = 0;

String myChan = "c3"; 


void WiFiEvent(WiFiEvent_t event){
    switch(event) {
      case SYSTEM_EVENT_STA_GOT_IP:
          Serial.print("WiFi connected! IP address: ");
          Serial.println(WiFi.localIP());  
          wifiOK = true;
          break;
      case SYSTEM_EVENT_STA_DISCONNECTED:
          Serial.println("WiFi lost connection");
          wifiOK = false;
          break;
    }
}


void onDmxFrame(uint16_t universe, uint16_t length, uint8_t sequence, uint8_t* data)
{
  boolean tail = false;
  
  Serial.print("DMX: Univ: ");
  Serial.print(universe, DEC);
  Serial.print(", Seq: ");
  Serial.print(sequence, DEC);
  Serial.print(", Data (");
  Serial.print(length, DEC);
  Serial.print("): ");
  
  if (length > 16) {
    length = 16;
    tail = true;
  }
  // send out the buffer
  for (int i = 0; i < length; i++)
  {
    Serial.print(data[i], HEX);
    Serial.print(" ");
  }
  if (tail) {
    Serial.print("...");
  }
  Serial.println();
}


void splitString(char* data, char* separator, int index, char* result)
{   
    char input[strlen(data)];
    strcpy(input, data);

    char* command = strtok(input, separator);
    for (int k=0; k<index; k++)
      if (command != NULL) command = strtok(NULL, separator);
    
    if (command == NULL) strcpy(result, "");
    else strcpy(result, command);
}



void callback(char* topic, byte* payload, unsigned int length) {
  
  payload[length] = 0;

  // ENGINE
  char engine[16];
  splitString(topic, "/", 0, engine);

  // OSC
  if (strcmp(engine, "osc") == 0) {
    Serial.print("OSC : ");
    Serial.print(topic);
    Serial.print(" ");
       
    char val[128];
    byte inc =0;
    splitString((char*)payload, "§", inc, val);
    while (strcmp(val, "") != 0) {
      Serial.print(val);
      Serial.print(" ");
      ++inc;
      splitString((char*)payload, "§", inc, val);
    }
    Serial.println("");

  }

  // MIDI
  if (strcmp(engine, "midi") == 0) {
    Serial.print("MIDI: ");
    Serial.print(topic);
    Serial.print(" ");

    char val[16];
    splitString((char*)payload, "-", 0, val);
    Serial.print(atoi(val));
    Serial.print(" ");
    splitString((char*)payload, "-", 1, val);
    Serial.print(atoi(val));
    Serial.print(" ");
    splitString((char*)payload, "-", 2, val);
    Serial.print(atoi(val));
    Serial.print(" ");
    Serial.println("");

  }

}


void reconnect() {
  // Loop until we're reconnected
  while (!client.connected() && wifiOK) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP32-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish("esp", "hello world");
      // ... and resubscribe
      client.subscribe( ("midi/"+myChan).c_str(), 1);
      client.subscribe( "midi/sys", 1);
      client.subscribe( "midi/all", 1);
      client.subscribe( ("osc/"+myChan+"/#").c_str(), 1);
      client.subscribe( "osc/all", 1);

      artnet.begin();
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(BUILTIN_LED, OUTPUT);
  randomSeed(micros());

  // WIFI
  Serial.println("Connecting wifi..");
  WiFi.disconnect(true);
  WiFi.onEvent(WiFiEvent);
  WiFi.begin("kxkm-wifi", "KOMPLEXKAPHARNAUM");
  
  // MQTT Client
  Serial.println("Connecting mqtt..");
  client.setServer("10.2.7.131", 1883);
  client.setCallback(callback);

  // ARTNET
  artnet.setArtDmxCallback(onDmxFrame);

}

void loop() {

  reconnect();
  client.loop();
  artnet.read();

  long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;
    ++value;
    snprintf (msg, 50, "hello world #%ld", value);
    // Serial.print("Publish message: ");
    // Serial.println(msg);
    client.publish("esp", msg);
  }

}


