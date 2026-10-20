# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root=Path(SPECPATH)
datas=[]
for n in ['motorsport_hero.jpg','motorsport_preview.jpg','motorsport_sidebar.jpg','sorg_full_logo.jpg','sorg_gt.ico']:
    if (root/n).exists(): datas.append((str(root/n), '.'))
a=Analysis(['main.py'], pathex=[str(root)], binaries=[], datas=datas,
           hiddenimports=['report_generator','updater_client','dialogs','database'],
           hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='SORG_GT_Data_Analyzer',debug=False,
        bootloader_ignore_signals=False,strip=False,upx=True,console=False,
        icon=str(root/'sorg_gt.ico') if (root/'sorg_gt.ico').exists() else None)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=True,upx_exclude=[],name='SORG GT Data Analyzer')
