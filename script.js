const formulario = document.getElementById("formulario");
const nombre = document.getElementById("nombre");
const descripcion = document.getElementById("descripcion");
const categoria = document.getElementById("categoria");

const errorNombre = document.getElementById("errorNombre");
const errorDescripcion = document.getElementById("errorDescripcion");
const errorCategoria = document.getElementById("errorCategoria");

const lista = document.getElementById("lista");
const mensaje = document.getElementById("mensaje");
const total = document.getElementById("total");

let contador = 0;
let actividades = [];

/* SERVICIOS DINÁMICOS */

const servicios = [
    "Guías de estudio",
    "Planificación de tareas",
    "Consejos de productividad",
    "Herramientas digitales"
];

const contenedorServicios =
document.getElementById("contenedorServicios");

servicios.forEach(servicio => {

    contenedorServicios.innerHTML += `
        <div class="col-md-3">
            <div class="card p-3 text-center m-2">
                ${servicio}
            </div>
        </div>
    `;

});

function validarNombre() {
    if (nombre.value.trim().length < 3) {
        nombre.classList.add("is-invalid");
        nombre.classList.remove("is-valid");

        errorNombre.innerHTML =
            '<div class="alert alert-danger py-1">Ingrese mínimo 3 caracteres.</div>';

        return false;
    }

    nombre.classList.add("is-valid");
    nombre.classList.remove("is-invalid");

    errorNombre.innerHTML =
        '<div class="alert alert-success py-1">Nombre válido.</div>';

    return true;
}

function validarDescripcion() {
    if (descripcion.value.trim().length < 10) {
        descripcion.classList.add("is-invalid");
        descripcion.classList.remove("is-valid");

        errorDescripcion.innerHTML =
            '<div class="alert alert-danger py-1">Ingrese al menos 10 caracteres.</div>';

        return false;
    }

    descripcion.classList.add("is-valid");
    descripcion.classList.remove("is-invalid");

    errorDescripcion.innerHTML =
        '<div class="alert alert-success py-1">Descripción válida.</div>';

    return true;
}

function validarCategoria() {
    if (categoria.value === "") {
        categoria.classList.add("is-invalid");
        categoria.classList.remove("is-valid");

        errorCategoria.innerHTML =
            '<div class="alert alert-danger py-1">Seleccione una categoría.</div>';

        return false;
    }

    categoria.classList.add("is-valid");
    categoria.classList.remove("is-invalid");

    errorCategoria.innerHTML =
        '<div class="alert alert-success py-1">Categoría seleccionada.</div>';

    return true;
}

nombre.addEventListener("input", validarNombre);
nombre.addEventListener("blur", validarNombre);

descripcion.addEventListener("input", validarDescripcion);
descripcion.addEventListener("blur", validarDescripcion);

categoria.addEventListener("change", validarCategoria);
categoria.addEventListener("blur", validarCategoria);

formulario.addEventListener("submit", function(e) {

    e.preventDefault();

    const nombreValido = validarNombre();
    const descripcionValida = validarDescripcion();
    const categoriaValida = validarCategoria();

    if (!nombreValido || !descripcionValida || !categoriaValida) {

        mensaje.innerHTML =
            '<div class="alert alert-danger">Corrija los errores antes de registrar.</div>';

        return;
        
    }
const nuevaActividad = {
    nombre: nombre.value,
    descripcion: descripcion.value,
    categoria: categoria.value
};

actividades.push(nuevaActividad);

    const item = document.createElement("li");

    item.className =
        "list-group-item d-flex justify-content-between align-items-center";

    item.innerHTML =
        `${nombre.value} - ${descripcion.value} (${categoria.value})`;

    const botonEliminar = document.createElement("button");

    botonEliminar.textContent = "Eliminar";
    botonEliminar.className = "btn btn-danger btn-sm";

    botonEliminar.addEventListener("click", function() {

    lista.removeChild(item);
    actividades.pop();

    contador--;

    total.textContent = contador;

    if (contador === 0) {

        mensaje.innerHTML =
            '<div class="alert alert-warning">No existen registros.</div>';
    }
});

    item.appendChild(botonEliminar);

    lista.appendChild(item);

    contador++;

    total.textContent = contador;

   if (contador > 0) {

    mensaje.innerHTML =
        `<div class="alert alert-success">
            Existen ${contador} registros almacenados.
        </div>`;
}

    formulario.reset();

    nombre.classList.remove("is-valid");
    descripcion.classList.remove("is-valid");
    categoria.classList.remove("is-valid");

    errorNombre.innerHTML = "";
    errorDescripcion.innerHTML = "";
    errorCategoria.innerHTML = "";
});