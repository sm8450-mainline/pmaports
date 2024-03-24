# Various GPU workarounds for Adreno a506

# The 'ngl' GTK renderer, which is now used by default, has worse
# performance and is somewhat more prone to crashes. Use the 'gl'
# renderer until these issues have been sorted out.
#
# https://gitlab.gnome.org/GNOME/gtk/-/issues/6576
export GSK_RENDERER=gl
