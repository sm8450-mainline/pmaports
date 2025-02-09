# Various GPU workarounds for Adreno a506

# Use the 'ngl' GTK renderer, so we prepare for the removal of
# the legacy GL renderer
export GSK_RENDERER=ngl
