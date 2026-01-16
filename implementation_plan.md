# 📱 Mobile App Implementation Plan (PWA)

> **Goal:** Establish a "Hello World" Progressive Web App (PWA) managed by Antigravity agents, enabling rapid "Vibe Coding" and agentic control.

## User Review Required

> [!IMPORTANT]
> **Stack Decision:** This plan proceeds with **PWA (Progressive Web App)** as the primary mobile stack based on Phase 2 research. This offers the best "Agent-Friendliness" and rapid iteration cycles.
> **Fallback:** If native stores (App Store/Play Store) are mandatory *immediately*, we must switch to React Native (Expo) at the cost of higher agent friction.

## Proposed Changes

### 1. Project Initialization
- Create `src/mobile_app_pwa/` directory.
- Initialize a **Vite + React** project with PWA capabilities.
- [NEW] `src/mobile_app_pwa/vite.config.js` (PWA plugin config)
- [NEW] `src/mobile_app_pwa/manifest.json` (Mobile identity)

### 2. Antigravity Integration
- Create a simple "Bridge" to allow agents to control the app content.
- [NEW] `src/antigravity_core/mobile_bridge.py` (Simple API to serve content to the PWA).

### 3. CI/CD Setup
- Define a build command in `package.json` that agents can invoke reliably.

## Phase 3 & 4 Tasks (Execution)

### Phase 3: Integration Design
- [ ] Define the JSON schema for the "App Config" that agents will edit.
- [ ] Create the `mobile_bridge` to read this config.

### Phase 4: Prototyping
- [ ] Run `npm create vite@latest` (via agent).
- [ ] Implement `vite-plugin-pwa`.
- [ ] Deploy to local server and test "Install App".

## Verification Plan

### Automated Tests
- **Build Verification:**
  ```bash
  cd src/mobile_app_pwa && npm run build
  ```
  Expected: Exit code 0, `dist/` folder created.

- **Lighthouse PWA Check:**
  Run Lighthouse CLI against the local dev server to ensure PWA criteria are met (Manifest, Service Worker).

### Manual Verification
- **Browser Subagent:**
  - Launch browser.
  - Navigate to `http://localhost:5173`.
  - distinct "Install" icon/prompt availability.
