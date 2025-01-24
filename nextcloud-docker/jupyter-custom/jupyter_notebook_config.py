# Configuration file for jupyter-notebook.

c = get_config()
c.NotebookApp.allow_origin = '*'
c.NotebookApp.tornado_settings = {
    'headers': { 'Content-Security-Policy': "frame-ancestors *;" }
}
