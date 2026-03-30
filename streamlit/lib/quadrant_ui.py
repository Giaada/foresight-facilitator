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

    return f"""
    <div style="position: relative; width: 140px; height: 140px; margin: 40px auto; font-family: ui-sans-serif, system-ui, sans-serif; flex-shrink: 0;">
      <!-- Testi Asse Y -->
      <div style="position: absolute; top: -30px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: bold; color: #64748b; white-space: nowrap; text-transform: capitalize;">{v_asse_y_pos}</div>
      <div style="position: absolute; bottom: -30px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: bold; color: #64748b; white-space: nowrap; text-transform: capitalize;">{v_asse_y_neg}</div>
      
      <!-- Testi Asse X -->
      <div style="position: absolute; top: 50%; left: -20px; transform: translateY(-50%) translateX(-100%) rotate(180deg); writing-mode: vertical-rl; font-size: 11px; font-weight: bold; color: #64748b; white-space: nowrap; text-transform: capitalize;">{v_asse_x_neg}</div>
      <div style="position: absolute; top: 50%; right: -20px; transform: translateY(-50%) translateX(100%); writing-mode: vertical-rl; font-size: 11px; font-weight: bold; color: #64748b; white-space: nowrap; text-transform: capitalize;">{v_asse_x_pos}</div>

      <!-- Sfondo Quadranti -->
      <div style="position: absolute; inset: 0; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; z-index: 0; outline: 1px solid transparent;">
         <div style="background-color: {bg_tl}; box-shadow: {shadow_tl}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_tl}; font-size: 16px; border-radius: 6px 0 0 0; transition: background-color 0.2s;">-+</div>
         <div style="background-color: {bg_tr}; box-shadow: {shadow_tr}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_tr}; font-size: 16px; border-radius: 0 6px 0 0; transition: background-color 0.2s;">++</div>
         <div style="background-color: {bg_bl}; box-shadow: {shadow_bl}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_bl}; font-size: 16px; border-radius: 0 0 0 6px; transition: background-color 0.2s;">--</div>
         <div style="background-color: {bg_br}; box-shadow: {shadow_br}; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold; color: {color_br}; font-size: 16px; border-radius: 0 0 6px 0; transition: background-color 0.2s;">+-</div>
      </div>

      <!-- Linea e frecce Asse Y -->
      <div style="position: absolute; left: 50%; top: -14px; bottom: -14px; width: 3px; background-color: #1e293b; transform: translateX(-50%); z-index: 10;"></div>
      <div style="position: absolute; left: 50%; top: -18px; width: 0; height: 0; border-left: 7px solid transparent; border-right: 7px solid transparent; border-bottom: 10px solid #1e293b; transform: translateX(-50%); z-index: 10;"></div>
      <div style="position: absolute; left: 50%; bottom: -18px; width: 0; height: 0; border-left: 7px solid transparent; border-right: 7px solid transparent; border-top: 10px solid #1e293b; transform: translateX(-50%); z-index: 10;"></div>

      <!-- Linea e frecce Asse X -->
      <div style="position: absolute; top: 50%; left: -14px; right: -14px; height: 3px; background-color: #1e293b; transform: translateY(-50%); z-index: 10;"></div>
      <div style="position: absolute; top: 50%; right: -18px; width: 0; height: 0; border-top: 7px solid transparent; border-bottom: 7px solid transparent; border-left: 10px solid #1e293b; transform: translateY(-50%); z-index: 10;"></div>
      <div style="position: absolute; top: 50%; left: -18px; width: 0; height: 0; border-top: 7px solid transparent; border-bottom: 7px solid transparent; border-right: 10px solid #1e293b; transform: translateY(-50%); z-index: 10;"></div>
    </div>
    """
