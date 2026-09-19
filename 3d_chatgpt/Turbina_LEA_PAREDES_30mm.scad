/*
  Turbina centrifuga para LEA_PAREDES
  Motor: coreless 8520

  Dimensiones principales:
    - Diametro exterior: 30.0 mm
    - Altura total: 6.3 mm
    - Disco posterior: 1.5 mm
    - Altura de aspas: 4.8 mm
    - Cantidad de aspas: 6
    - Orificio del eje: 1.54 mm nominal
    - Profundidad del orificio: 5.15 mm (ciego)

  El sentido se define mirando la turbina desde el lado del motor/disco.
  Valores permitidos: "CCW" o "CW".
*/

$fn = 160;

rotation_direction = "CCW";

impeller_diameter = 30.0;
backplate_thickness = 1.5;
blade_height = 4.8;
blade_count = 6;
blade_thickness = 1.0;
blade_inner_radius = 3.0;
blade_outer_radius = 14.35;
blade_sweep_degrees = 34;
hub_diameter = 6.5;
shaft_hole_diameter = 1.54;
shaft_hole_depth = 5.15;

total_height = backplate_thickness + blade_height;

// El observador esta del lado del motor (cara plana, z negativo).
// Esa vista invierte el sentido aparente respecto de la vista de las aspas.
direction_sign = rotation_direction == "CCW" ? 1 : -1;

module polar_disc(radius, angle, diameter, height) {
    translate([radius * cos(angle), radius * sin(angle), backplate_thickness])
        cylinder(d = diameter, h = height, $fn = 24);
}

// Aspa curvada hacia atras, construida mediante segmentos tangentes.
module curved_blade_2d() {
    steps = 12;
    for (index = [0 : steps - 1]) {
        radius_1 = blade_inner_radius
            + (blade_outer_radius - blade_inner_radius) * index / steps;
        radius_2 = blade_inner_radius
            + (blade_outer_radius - blade_inner_radius) * (index + 1) / steps;

        // Curvatura progresiva: suave en la entrada y mas marcada en la salida.
        progress_1 = index / steps;
        progress_2 = (index + 1) / steps;
        angle_1 = direction_sign * blade_sweep_degrees * progress_1 * progress_1;
        angle_2 = direction_sign * blade_sweep_degrees * progress_2 * progress_2;

        hull() {
            translate([radius_1 * cos(angle_1), radius_1 * sin(angle_1)])
                circle(d = blade_thickness, $fn = 20);
            translate([radius_2 * cos(angle_2), radius_2 * sin(angle_2)])
                circle(d = blade_thickness, $fn = 20);
        }
    }
}

module impeller_body() {
    union() {
        // Disco cerrado que recibe el eje del motor.
        cylinder(d = impeller_diameter, h = backplate_thickness);

        // Cubo central: une las seis aspas y refuerza el alojamiento del eje.
        cylinder(d = hub_diameter, h = total_height);

        // Seis aspas equidistantes para conservar el balance dinamico.
        for (blade = [0 : blade_count - 1]) {
            rotate([0, 0, blade * 360 / blade_count])
                translate([0, 0, backplate_thickness])
                    linear_extrude(height = blade_height)
                        curved_blade_2d();
        }
    }
}

difference() {
    impeller_body();

    // Alojamiento ciego: entrada desde la cara plana del disco.
    // Se deja material en el extremo para que el eje no atraviese la turbina.
    translate([0, 0, -0.05])
        cylinder(d = shaft_hole_diameter,
                 h = shaft_hole_depth + 0.05,
                 $fn = 64);
}
