'''
SOAP Server
Made by Let's Shop & Ghost Land Team! 2024
'''
print("Shopdeck Server - SOAP XML Services\n\nBy Let's Shop Team 2024 and Ghost Land Team 2024\n\n\n")
print("----------------------------------")

from flask import Flask
import ecs, ias, cas, cdn, assetcdn

app = Flask(__name__)
app.register_blueprint(ecs.ecs)
app.register_blueprint(ias.ias)
app.register_blueprint(cas.cas)
app.register_blueprint(cdn.ccs)
app.register_blueprint(assetcdn.cdn)

print("READY!")