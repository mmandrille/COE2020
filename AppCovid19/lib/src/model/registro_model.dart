///
/// Model Registro
/// @author JLopez
///
class RegistroModel {
  String localidadNombre;
  String email;
  String direccionNumero;
  String apellido;
  String dniIndividuo;
  String nombre;
//  String pushNotificationId;
  String telefono;
  String direccionCalle;

  RegistroModel({
    this.localidadNombre,
    this.email,
    this.direccionNumero,
    this.apellido,
    this.dniIndividuo,
    this.nombre,
//    this.pushNotificationId,
    this.telefono,
    this.direccionCalle,
  });

  factory RegistroModel.fromJson(Map<String, dynamic> json) => RegistroModel(
    localidadNombre: json["localidad_nombre"],
    email: json["email"],
    direccionNumero: json["direccion_numero"],
    apellido: json["apellido"],
    dniIndividuo: json["dni_individuo"],
    nombre: json["nombre"],
//    pushNotificationId: json["push_notification_id"],
    telefono: json["telefono"],
    direccionCalle: json["direccion_calle"],
  );

  Map<String, dynamic> toJson() => {
    "localidad_nombre": localidadNombre,
    "email": email,
    "direccion_numero": direccionNumero,
    "apellido": apellido,
    "dni_individuo": dniIndividuo,
    "nombre": nombre,
//    "push_notification_id": pushNotificationId,
    "telefono": telefono,
    "direccion_calle": direccionCalle,
  };
}
