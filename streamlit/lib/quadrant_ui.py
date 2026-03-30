def draw_quadrant_matrix(quadrante, asse_x_pos, asse_x_neg, asse_y_pos, asse_y_neg):
    bg_tl = "rgba(79, 70, 229, 0.15)" if quadrante == "-+" else "#f8fafc"
    bg_tr = "rgba(79, 70, 229, 0.15)" if quadrante == "++" else "#f8fafc"
    bg_bl = "rgba(79, 70, 229, 0.15)" if quadrante == "--" else "#f8fafc"
    bg_br = "rgba(79, 70, 229, 0.15)" if quadrante == "+-" else "#f8fafc"
    color_tl = "rgba(49, 46, 129, 0.6)" if quadrante == "-+" else "#cbd5e1"
    color_tr = "rgba(49, 46, 129, 0.6)" if quadrante == "++" else "#cbd5e1"
    color_bl = "rgba(49, 46, 129, 0.6)" if quadrante == "--" else "#cbd5e1"
    color_br = "rgba(49, 46, 129, 0.6)" if quadrante == "+-" else "#cbd5e1"
    shadow_tl = "inset 0 2px 4px 0 rgba(0,0,0,0.06)" if quadrante == "-+" else "none"
    shadow_tr = "inset 0 2px 4px 0 rgba(0,0,0,0.06)" if quadrante == "++" else "none"
    shadow_bl = "inset 0 2px 4px 0 rgba(0,0,0,0.06)" if quadrante == "--" else "none"
    shadow_br = "inset 0 2px 4px 0 rgba(0,0,0,0.06)" if quadrante == "+-" else "none"
    
    v_asse_x_pos = asse_x_pos or "Alto"
    v_asse_x_neg = asse_x_neg or "Basso"
    v_asse_y_pos = asse_y_pos or "Alto"
    v_asse_y_neg = asse_y_neg or "Basso"

    # Labels are all horizontal, wrapping allowed (no white-space: nowrap)
    # Arrows only on top (Y+) and right (X+) like a Cartesian plane
    return f"""
    <div style="position: relative; width: 160px; height: 160px; margin: 35px 50px; font-family: ui-sans-serif, system-ui, sans-serif; flex-shrink: 0;">
      <!-- Label Asse Y: top (+) and bottom (-), horizontal -->
      <div style="position: absolute; bottom: calc(100% + 22px); left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: center; max-width: 100px; line-height: 1.2; display: flex; align-items: flex-end; justify-content: center;">{v_asse_y_pos}</div>
      <div style="position: absolute; top: calc(100% + 8px); left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: center; max-width: 100px; line-height: 1.2; display: flex; align-items: flex-start; justify-content: center;">{v_asse_y_neg}</div>
      
      <!-- Label Asse X: left (-) and right (+), horizontal -->
      <div style="position: absolute; top: 50%; right: calc(100% + 8px); transform: translateY(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: right; max-width: 70px; line-height: 1.2;">{v_asse_x_neg}</div>
      <div style="position: absolute; top: 50%; left: calc(100% + 24px); transform: translateY(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: left; max-width: 70px; line-height: 1.2;">{v_asse_x_pos}</div>

      <!-- Sfondo Quadranti -->
      <div style="position: absolute; inset: 0; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; z-index: 0; outline: 1px solid transparent;">
         <div style="background-color: {bg_tl}; box-shadow: {shadow_tl}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_tl}; font-size: 16px; border-radius: 6px 0 0 0; transition: background-color 0.2s;">-+</div>
         <div style="background-color: {bg_tr}; box-shadow: {shadow_tr}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_tr}; font-size: 16px; border-radius: 0 6px 0 0; transition: background-color 0.2s;">++</div>
         <div style="background-color: {bg_bl}; box-shadow: {shadow_bl}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_bl}; font-size: 16px; border-radius: 0 0 0 6px; transition: background-color 0.2s;">--</div>
         <div style="background-color: {bg_br}; box-shadow: {shadow_br}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_br}; font-size: 16px; border-radius: 0 0 6px 0; transition: background-color 0.2s;">+-</div>
      </div>

      <!-- Asse Y: linea verticale + freccia SOLO in alto -->
      <div style="position: absolute; left: 50%; top: -14px; bottom: -4px; width: 3px; background-color: #1e293b; transform: translateX(-50%); z-index: 10;"></div>
      <div style="position: absolute; left: 50%; top: -18px; width: 0; height: 0; border-left: 7px solid transparent; border-right: 7px solid transparent; border-bottom: 10px solid #1e293b; transform: translateX(-50%); z-index: 10;"></div>

      <!-- Asse X: linea orizzontale + freccia SOLO a destra -->
      <div style="position: absolute; top: 50%; left: -4px; right: -14px; height: 3px; background-color: #1e293b; transform: translateY(-50%); z-index: 10;"></div>
      <div style="position: absolute; top: 50%; right: -18px; width: 0; height: 0; border-top: 7px solid transparent; border-bottom: 7px solid transparent; border-left: 10px solid #1e293b; transform: translateY(-50%); z-index: 10;"></div>
    </div>
    """
