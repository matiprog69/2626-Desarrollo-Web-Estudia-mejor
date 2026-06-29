const formulario = document.getElementById("formulario");
const nombre = document.getElementById("nombre");
const descripcion = document.getElementById("descripcion");
const categoria = document.getElementById("categoria");
const lista = document.getElementById("lista");
const mensaje = document.getElementById("mensaje");
const total = document.getElementById("total");

let contador = 0;

formulario.addEventListener("submit", function(e) {
    e.preventDefault(); // 

    // VALIDACIÓN
    if (nombre.value === "" || descripcion.value === "" || categoria.value === "") {
        mensaje.innerHTML = "<div class='alert alert-danger'>Todos los campos son obligatorios</div>";
        return;
    }

    mensaje.innerHTML = "";

    // CREAR ELEMENTOS
    const item = document.createElement("li");
    item.className = "list-group-item d-flex justify-content-between align-items-center";

    item.innerHTML = `
        <span>
            <strong>${nombre.value}</strong> - ${descripcion.value} (${categoria.value})
        </span>
    `;

    // BOTÓN ELIMINAR
    const botonEliminar = document.createElement("button");
    botonEliminar.textContent = "Eliminar";
    botonEliminar.className = "btn btn-danger btn-sm";

    botonEliminar.addEventListener("click", function() {
        lista.removeChild(item);
        contador--;
        total.textContent = contador;
    });

    // AGREGAR BOTÓN
    item.appendChild(botonEliminar);

    // AGREGAR A LISTA
    lista.appendChild(item);

    // ACTUALIZAR CONTADOR
    contador++;
    total.textContent = contador;

    // LIMPIAR FORM
    formulario.reset();
});
