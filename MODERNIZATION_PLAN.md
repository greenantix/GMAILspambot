# GUI Modernization Plan: React + Tauri

This document outlines the architectural plan to modernize the existing application by wrapping the React frontend in a Tauri desktop shell.

## 1. Technology Recommendation: Tauri

For this project, **Tauri** is recommended over Electron for the following reasons:

*   **Lightweight & Fast:** Tauri applications are significantly smaller and use less memory because they leverage the operating system's built-in webview instead of bundling a full browser.
*   **Secure:** Tauri is built with a security-first mindset, enabling modern security features by default to protect against common web vulnerabilities.
*   **Backend Agnostic:** Tauri's "sidecar" feature allows it to manage and communicate with external processes, making it ideal for running the existing Python backend seamlessly.

## 2. Modernization Phases

The project will be broken down into three distinct phases:

### Phase 1: Desktop Integration (Tauri Setup)

The goal of this phase is to get the existing React application running inside a Tauri desktop window.

1.  **Prerequisites:** Install Rust, Node.js, and any other system dependencies required by Tauri.
2.  **Integrate Tauri:** Add Tauri to the existing `frontend/` directory. This will scaffold a new `src-tauri` directory to house the desktop-specific configuration and Rust code.
3.  **Configure Sidecar:** Modify `tauri.conf.json` to manage the Python API server as a sidecar. Tauri will be responsible for starting and stopping the Python backend process.
4.  **Development Setup:** Configure Tauri's development server to proxy requests to the React development server (e.g., `http://localhost:3000`) to enable hot-reloading for the frontend.

### Phase 2: UI/UX Overhaul

With the application running on the desktop, this phase focuses on modernizing the user interface.

1.  **Component Library:** Integrate a modern, unstyled component library like **Shadcn/ui**. It works seamlessly with the project's existing Tailwind CSS setup and provides a solid foundation for a clean UI.
2.  **Component Refactoring:** Systematically refactor existing React components to use the new component library and improve their design.
    *   **Dashboard:** Redesign for better data visualization and a cleaner layout.
    *   **Settings:** Improve form layouts and overall user experience.
    *   **Shared Components:** Update buttons, cards, and icons for a consistent, modern look across the application.
3.  **Native Features:** Enhance the user experience by adding desktop-specific features using Tauri's API:
    *   **Desktop Notifications:** For build completions, errors, or other important events.
    *   **System Tray Icon:** Allow the application to run in the background.
    *   **Native Menus:** Implement standard application menus (`File`, `Edit`, `View`, etc.).

### Phase 3: Build & Distribution

This final phase prepares the application for release.

1.  **Unified Build Process:** Create a single script that builds the production-optimized React frontend and then runs the Tauri build process to package the final application.
2.  **Native Installers:** The Tauri build process will automatically generate native installers for major operating systems (e.g., `.msi` for Windows, `.app`/`.dmg` for macOS, and `.deb`/`.AppImage` for Linux), simplifying distribution.