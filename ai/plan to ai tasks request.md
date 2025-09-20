


### **UCore Framework: Example Application Generation Plan**

**Objective:** To create a series of self-contained, runnable example applications that demonstrate the framework's key features in realistic scenarios. These examples will serve as documentation, tutorials, and a basis for end-to-end testing.
place examples to:D:\UCore\example

---

### **Example 1: "QuickTask" - A Simple CLI To-Do Application**

**Goal:** Demonstrate the absolute basics of the framework: the application lifecycle, dependency injection, and component registration in a non-web context.

**Features Covered:**
*   `core/app.py`: `App` class and lifecycle.
*   `core/component.py`: Basic `Component` implementation.
*   `core/di.py`: Registering and getting a simple service.
*   `core/processing/cli.py`: Basic integration with `typer` for commands.

**LLM Instructions for Implementation:**

1.  **Create Project Structure:**
    *   Create a new directory named `examples/quicktask/`.
    *   Inside, create `quicktask/main.py` and `quicktask/task_service.py`.

2.  **Implement `task_service.py`:**
    *   Define a class `TaskService`.
    *   Give it an in-memory list to store tasks (e.g., `self._tasks = []`).
    *   Implement methods `add_task(description: str)`, `list_tasks() -> list`, and `complete_task(index: int)`.

3.  **Implement `main.py`:**
    *   Import `App`, `Component`, `Container`, and `typer`.
    *   Import `TaskService`.
    *   **Define `TaskComponent(Component)`:**
        *   In its `start` method, get the `TaskService` from the container and log a message.
    *   **Define CLI Commands:**
        *   Create a `typer` app instance.
        *   Define a command `add(description: str)` that gets the `TaskService` from the main app's container and calls `add_task`.
        *   Define a command `list()` that gets the service and prints the tasks.
    *   **Define the Main Application Block (`if __name__ == "__main__":`)**
        *   Instantiate `app = App("QuickTask")`.
        *   Register the `TaskService` as a singleton in the app's container: `app.container.register(TaskService, scope=Scope.SINGLETON)`.
        *   Register the `TaskComponent`.
        *   Run the `typer` CLI app.

---

### **Example 2: "ImageGallery" - A Web API and Background Worker**

**Goal:** Demonstrate a full-stack web application with an API, background processing, and database interaction. This is the core "real-world" example.

**Features Covered:**
*   `web/http.py`: `HttpServer` with route handling.
*   `data/mongo_orm.py`: `BaseMongoRecord` for data modeling.
*   `core/processing/tasks.py`: Celery tasks for background work.
*   `fs/resource.py`: Using `FilesDBResource` for file metadata.
*   `monitoring/observability.py`: Adding metrics to API endpoints.
*   `core/resource/manager.py`: Managing database and other resources.

**LLM Instructions for Implementation:**

1.  **Create Project Structure:**
    *   Create `examples/imagegallery/`.
    *   Inside, create `imagegallery/main.py`, `imagegallery/models.py`, `imagegallery/api.py`, `imagegallery/tasks.py`, and a `config.yml`.

2.  **Implement `config.yml`:**
    *   Add configuration for MongoDB (`database.mongodb.url`), Redis (`CELERY_BROKER_URL`), and the HTTP server (`HTTP_PORT`).

3.  **Implement `models.py`:**
    *   Define an `ImageRecord(BaseMongoRecord)` with fields like `filename: str`, `status: str` (e.g., "processing", "completed"), and `thumbnail_path: str`.
    *   Set the `collection_name`.

4.  **Implement `tasks.py`:**
    *   Import the Celery `task` decorator and `ImageRecord`.
    *   Define a task `generate_thumbnail(image_id: str)`.
    *   Inside the task, simulate image processing (e.g., `time.sleep(2)`).
    *   Update the `ImageRecord` in the database: find the record by `image_id`, change its `status` to "completed", and set a `thumbnail_path`.

5.  **Implement `api.py`:**
    *   Instantiate an `HttpServer` component.
    *   Define a `GET /images` route that uses `ImageRecord.find()` to list all images.
    *   Define a `POST /images` route that:
        *   Saves an uploaded file to a temporary directory.
        *   Creates an `ImageRecord` with `status="processing"`.
        *   Dispatches the `generate_thumbnail` background task with the new image's ID.
        *   Returns a `202 Accepted` response with the new image's ID.

6.  **Implement `main.py`:**
    *   Create an `App("ImageGallery")`.
    *   **Register Components:** Register `HttpServer`, `TaskQueueAdapter`, and a `ResourceManager`.
    *   **Register Resources:** Register `MongoDBResource`.
    *   **Bootstrap:** In the main block, call `app.bootstrap()` to load the `config.yml`.
    *   Run the application: `app.run()`.

---

### **Example 3: "LiveDashboard" - A Real-time UI with MVVM and Web Sockets**

**Goal:** Demonstrate the desktop and MVVM capabilities, showing how to build a responsive UI that reacts to real-time events from the framework's `EventBus`.

**Features Covered:**
*   `desktop/ui/pyside6_adapter.py`: Integrating a Qt GUI.
*   `mvvm/base.py`: `ViewModelBase` and `ObservableList`.
*   `mvvm/pyside6_helpers.py`: Using `ObservableListModel`.
*   `core/event_bus.py`: Subscribing to system events.
*   `core/redis_event_bridge.py`: Receiving events from other application instances.

**LLM Instructions for Implementation:**

1.  **Create Project Structure:**
    *   Create `examples/livedashboard/`.
    *   Inside, create `livedashboard/main.py`, `livedashboard/viewmodels.py`, `livedashboard/views.py`.

2.  **Implement `viewmodels.py`:**
    *   Import `ViewModelBase` and `ObservableList`.
    *   Define `DashboardViewModel(ViewModelBase)`.
    *   In its `__init__`, initialize an `ObservableList` for system events: `self.set_property("events", ObservableList())`.
    *   This ViewModel will be injected into the `EventMonitorComponent`.

3.  **Implement `views.py`:**
    *   Import `PySide6` components (`QMainWindow`, `QListView`, etc.) and `ObservableListModel`.
    *   Define a `DashboardWindow(QMainWindow)`.
    *   The window should contain a `QListView`.
    *   Implement a `bind_viewmodel(self, viewmodel)` method that:
        *   Creates an `ObservableListModel` from the ViewModel's `events` property.
        *   Sets this model on the `QListView`.

4.  **Implement `main.py`:**
    *   Create an `App("LiveDashboard")`.
    *   **Define `EventMonitorComponent(Component)`:**
        *   In its `__init__`, it should accept the `DashboardViewModel`.
        *   In its `start` method, get the `EventBus` from the container.
        *   Subscribe to a general system event (e.g., `CoreEvent`). The handler for this event should append a descriptive string of the event to the `DashboardViewModel`'s `events` list.
    *   **Main Block:**
        *   Instantiate `DashboardViewModel`.
        *   Instantiate `DashboardWindow`.
        *   Instantiate and register `PySide6Adapter`.
        *   Instantiate and register `EventMonitorComponent(viewmodel)`.
        *   Bind the view and viewmodel.
        *   Show the window.
        *   Run the app.

---

### **Example 4: "PluginNotepad" - A Modular Text Editor**

**Goal:** Demonstrate the plugin system by creating a simple notepad application where different plugins can provide viewers for different file types (e.g., text, markdown).

**Features Covered:**
*   `core/plugins.py`: The `PluginManager`, `PluginRegistry`, and `@plugin` decorator.
*   `desktop/ui/tabbed_window.py`: Using a tabbed interface.
*   `mvvm/datatable.py`: Using `DataTemplate` to dynamically select the right viewer plugin.

**LLM Instructions for Implementation:**

1.  **Create Project Structure:**
    *   Create `examples/pluginnotepad/`.
    *   Inside, create `pluginnotepad/main.py`, `pluginnotepad/plugins/`.
    *   In `plugins/`, create `text_viewer_plugin.py` and `markdown_viewer_plugin.py`.

2.  **Implement `text_viewer_plugin.py`:**
    *   Import `Plugin`, `plugin`, `PluginType`, `QWidget`, `QTextEdit`.
    *   Define a `TextViewerWidget(QWidget)` that contains a `QTextEdit`.
    *   Use the `@plugin` decorator to define `TextViewerPlugin(Plugin)`.
    *   Set `plugin_type=PluginType.VIEWER` and `supported_formats=["txt", "py"]`.
    *   Implement a `create_widget(self, content: str) -> QWidget` method that returns an instance of `TextViewerWidget` displaying the content.

3.  **Implement `markdown_viewer_plugin.py`:**
    *   Similar to the text viewer, but use a `QTextBrowser` widget.
    *   The `create_widget` method should use `setMarkdown()` to render the content.
    *   Set `supported_formats=["md"]`.

4.  **Implement `main.py`:**
    *   Create the main application window, which will have a "File -> Open" menu.
    *   **Main App Logic:**
        *   Instantiate the `App`.
        *   Instantiate and register `PluginManager`.
        *   In the main block, call `plugin_manager.load_plugins("pluginnotepad/plugins")`.
    *   **"Open File" Logic:**
        *   When a file is opened, get its extension (e.g., `.txt` or `.md`).
        *   Use the `plugin_manager.registry` to find the appropriate viewer plugin by querying for `plugin_type=PluginType.VIEWER` and matching the `supported_formats`.
        *   Get an instance of the found plugin.
        *   Call the plugin's `create_widget(file_content)` method.
        *   Add the returned widget to a new tab in the main window.

This plan provides a structured approach to generating a powerful and educational set of examples, ensuring all major framework features are demonstrated in a practical context.