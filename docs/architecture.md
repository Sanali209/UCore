graph TD
    subgraph "Application Core"
        App(App Entry Point)
        App -- "Initializes and manages" --> CoreServices
    end

    subgraph "Core Services"
        CoreServices(Core Services)
        CoreServices -- "Manages component lifecycle" --> CompMgr(ComponentManager)
        CoreServices -- "Handles dependency injection" --> DI(DI Container)
        CoreServices -- "Manages event pub/sub" --> EvtBus(EventBus)
        CoreServices -- "Manages application configuration" --> CfgMgr(ConfigManager)
        CoreServices -- "Loads and manages plugins" --> PlugMgr(PluginManager)
    end

    subgraph "Components"
        CompMgr -- "Registers and manages" --> AbstractComp(Abstract Component)
        AbstractComp -- "Implemented by" --> WebComp(Web Component)
        AbstractComp -- "Implemented by" --> DesktopComp(Desktop Component)
        AbstractComp -- "Implemented by" --> DataComp(Data Component)
        AbstractComp -- "Implemented by" --> MonitoringComp(Monitoring Component)
        AbstractComp -- "Implemented by" --> FSComp(File System Component)
    end

    subgraph "Data Layer"
        DataComp -- "Uses" --> MongoAdapter(MongoDB Adapter)
        MongoAdapter -- "Manages" --> MongoORM(BaseMongoRecord ORM)
        MongoORM -- "Interacts with" --> MongoDB[(MongoDB)]
        note for MongoORM "Provides async CRUD operations and caching"
    end

    subgraph "Resource Management"
        App -- "Manages" --> ResMgr(ResourceManager)
        ResMgr -- "Manages" --> FileResource(File Resource)
        ResMgr -- "Manages" --> DBResource(Database Resource)
        ResMgr -- "Manages" --> APIResource(API Resource)
        note for ResMgr "Centralized management of all resources"
    end

    subgraph "Communication"
        EvtBus -- "Publishes" --> AppEvents(Application Events)
        EvtBus -- "Subscribes to" --> Handlers(Event Handlers)
        WebComp -- "Uses" --> EvtBus
        DesktopComp -- "Uses" --> EvtBus
        note for EvtBus "Decouples components through events"
    end

    subgraph "Plugins"
        PlugMgr -- "Loads" --> CustomPlugin(Custom Plugin)
        CustomPlugin -- "Extends" --> AbstractComp
        note for PlugMgr "Allows for dynamic extension of the framework"
    end

    subgraph "Desktop UI (PySide6)"
        DesktopComp -- "Uses" --> PySide6(PySide6 Adapter)
        PySide6 -- "Creates" --> MainWindow(Main Window)
        MainWindow -- "Uses" --> MVVM(MVVM Utilities)
        MVVM -- "Uses" --> DataProvider(Data Provider)
        DataProvider -- "Uses" --> MongoAdapter
        note for PySide6 "Integrates Qt event loop with asyncio"
    end

    subgraph "Web API"
        WebComp -- "Uses" --> HTTPServer(HTTP Server)
        HTTPServer -- "Defines" --> APIEndpoints(API Endpoints)
        APIEndpoints -- "Use" --> MVVM
        note for HTTPServer "Based on aiohttp for async requests"
    end

    subgraph "Monitoring"
        MonitoringComp -- "Uses" --> HealthChecker(Health Checker)
        MonitoringComp -- "Uses" --> MetricsCollector(Metrics Collector)
        MetricsCollector -- "Exports to" --> Prometheus[(Prometheus)]
        note for MonitoringComp "Provides observability into the application"
    end

    subgraph "File System"
        FSComp -- "Uses" --> FSResource(File System Resource)
        FSResource -- "Manages" --> FileRecord(FileRecord Model)
        note for FSComp "Abstracts file system operations"
    end

    style App fill:#f9f,stroke:#333,stroke-width:2px
    style CoreServices fill:#ccf,stroke:#333,stroke-width:2px
    style Components fill:#cfc,stroke:#333,stroke-width:2px
    style DataLayer fill:#fcf,stroke:#333,stroke-width:2px
    style "Resource Management" fill:#ffc,stroke:#333,stroke-width:2px
    style Communication fill:#cff,stroke:#333,stroke-width:2px
    style Plugins fill:#fec,stroke:#333,stroke-width:2px
    style "Desktop UI (PySide6)" fill:#eef,stroke:#333,stroke-width:2px
    style "Web API" fill:#efe,stroke:#333,stroke-width:2px
    style Monitoring fill:#eef,stroke:#333,stroke-width:2px
    style "File System" fill:#fde,stroke:#333,stroke-width:2px
