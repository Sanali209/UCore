from ucore_framework.core.app import App
from ucore_framework.core.resource.manager import ResourceManager
from ucore_framework.core.resource.types.mongodb import MongoDBResource
from ucore_framework.web.http import HttpServer
from example.imagegallery.api import create_http_server

def main():
    app = App("ImageGallery")
    # Register resources and components
    app.container.register(ResourceManager)
    app.container.register(MongoDBResource)
    
    # Create HTTP server with app instance
    http_server = create_http_server(app)
    app.register_component(http_server)
    
    # Bootstrap config
    import argparse
    args = argparse.Namespace(config="config.yml", log_level="INFO", plugins_dir=None)
    app.bootstrap(args)
    app.run()

if __name__ == "__main__":
    main()
