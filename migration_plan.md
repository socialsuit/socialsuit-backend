# Migration Plan for Separating Social Suit and Sparkr

This document outlines the step-by-step process to separate the current monorepo into three distinct projects: Social Suit, Sparkr, and a shared library.

## Target Structure

```
├── social-suit/
│   ├── services/
│   │   ├── api/
│   │   ├── models/
│   │   ├── tasks/
│   │   └── ...
│   ├── tests/
│   ├── main.py
│   ├── celery_app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── sparkr/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── core/
│   │   └── ...
│   ├── tests/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── fly.toml
└── shared/
    ├── auth/
    ├── database/
    ├── utils/
    └── README.md
```

## Phase 1: Project Separation

### Step 1: Create Initial Project Structure

1. Create the three main directories:
   ```
   mkdir social-suit sparkr shared
   ```

### Step 2: Move Social Suit Core Files

1. Create necessary subdirectories in social-suit:
   ```
   mkdir -p social-suit/services/api social-suit/services/models social-suit/services/tasks social-suit/tests
   ```

2. Copy main.py, celery_app.py, and other root files to social-suit:
   ```
   cp main.py social-suit/
   cp celery_app.py social-suit/
   cp requirements.txt social-suit/
   cp Dockerfile social-suit/
   cp docker-compose.yml social-suit/
   ```

3. Copy services directory content to social-suit:
   ```
   cp -r services/api/ social-suit/services/api/
   cp -r services/models/ social-suit/services/models/
   cp -r services/tasks/ social-suit/services/tasks/
   ```

4. Copy tests directory to social-suit:
   ```
   cp -r tests/ social-suit/tests/
   ```

### Step 3: Move Sparkr Core Files

1. Create necessary subdirectories in sparkr:
   ```
   mkdir -p sparkr/app/api sparkr/app/models sparkr/app/core sparkr/tests
   ```

2. Copy sparkr-backend files to sparkr:
   ```
   cp -r sparkr-backend/app/api/ sparkr/app/api/
   cp -r sparkr-backend/app/models/ sparkr/app/models/
   cp -r sparkr-backend/app/core/ sparkr/app/core/
   cp -r sparkr-backend/tests/ sparkr/tests/
   cp sparkr-backend/main.py sparkr/
   cp sparkr-backend/requirements.txt sparkr/
   cp sparkr-backend/Dockerfile sparkr/
   cp sparkr-backend/docker-compose.yml sparkr/
   cp sparkr-backend/fly.toml sparkr/
   ```

## Phase 2: Shared Component Extraction

### Step 1: Identify Shared Components

Analyze both projects to identify common components that should be moved to the shared library:

1. Authentication utilities
2. Database connection utilities
3. Common models and schemas
4. Utility functions

### Step 2: Extract Shared Components

1. Create necessary subdirectories in shared:
   ```
   mkdir -p shared/auth shared/database shared/utils
   ```

2. Move common authentication components:
   ```
   cp -r social-suit/services/api/auth/ shared/auth/
   ```

3. Move common database utilities:
   ```
   cp -r social-suit/services/models/database/ shared/database/
   ```

4. Move utility functions:
   ```
   cp -r social-suit/services/api/utils/ shared/utils/
   ```

5. Create README.md for shared library:
   ```
   touch shared/README.md
   ```

## Phase 3: Update Import Paths

### Step 1: Update Social Suit Import Paths

1. Update import statements in social-suit files to reference the new shared library
2. Replace imports like `from services.api.auth import X` with `from shared.auth import X`
3. Update internal imports to match the new structure (e.g., `from services.api import X`)

### Step 2: Update Sparkr Import Paths

1. Update import statements in sparkr files to reference the new shared library
2. Replace imports like `from app.core.auth import X` with `from shared.auth import X` where appropriate
3. Update internal imports to match the new structure (e.g., `from app.api import X`)

## Phase 4: Create Build and Test Verification

1. Create a script to verify that both projects build and run correctly after separation
2. Create a script to run tests for both projects to ensure functionality is preserved

## Phase 5: Documentation

1. Update README files for each project
2. Document the new architecture and dependencies between projects
3. Document the migration process and any manual steps required

## Best Practices for Ongoing Development

1. Use semantic versioning for the shared library
2. Establish clear ownership and contribution guidelines for shared components
3. Set up CI/CD pipelines for each project
4. Implement automated tests to ensure compatibility between projects