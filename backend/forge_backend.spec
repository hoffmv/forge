# PyInstaller spec file for FORGE backend
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules, collect_all

block_cipher = None

# Collect all pydantic and related packages
pydantic_imports = collect_submodules('pydantic')
pydantic_settings_imports = collect_submodules('pydantic_settings')
pydantic_core_imports = collect_submodules('pydantic_core')

# Collect all data files
datas = []
datas += collect_data_files('certifi')
datas += collect_data_files('pydantic')
datas += collect_data_files('pydantic_settings')
datas += collect_data_files('pydantic_core')

a = Analysis(
    ['app.py'],
    pathex=['backend'],
    binaries=collect_dynamic_libs('sqlite3'),
    datas=datas,
    hiddenimports=[
        # Uvicorn and async support
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Pydantic and settings
        'pydantic',
        'pydantic_settings',
        'pydantic_core',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        # Backend modules
        'backend.routers.health',
        'backend.routers.jobs',
        'backend.routers.settings',
        'backend.routers.upload',
        'backend.routers.workspace',
        'backend.routers.projects',
        'backend.routers.export',
        'backend.routers.help',
        'backend.services.orchestrator',
        'backend.services.llm_router',
        'backend.services.settings_service',
        'backend.services.conversational',
        'backend.providers.lmstudio',
        'backend.providers.openai_cloud',
        'backend.worker.queue_worker',
    ] + pydantic_imports + pydantic_settings_imports + pydantic_core_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='forge-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
