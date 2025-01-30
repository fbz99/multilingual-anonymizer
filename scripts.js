let selectedFile = null;

$(document).ready(function () {
  const dropZone = $("#dropZone");
  const fileInput = $("#fileInput");

  // Gestione del DRAG & DROP
  dropZone.on("dragenter", function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.addClass("hover");
  });

  dropZone.on("dragleave", function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.removeClass("hover");
  });

  dropZone.on("dragover", function(e) {
    e.preventDefault();
    e.stopPropagation();
  });

  dropZone.on("drop", function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.removeClass("hover");

    const files = e.originalEvent.dataTransfer.files;
    if (files && files.length > 0) {
      selectedFile = files[0];
      dropZone.text("File selezionato: " + selectedFile.name);
    }
  });

  // Apertura del selettore file
  $("#selectFileBtn").click(function() {
    fileInput.click();
  });

  // Quando l'utente seleziona un file via input
  fileInput.change(function(e) {
    if (e.target.files && e.target.files.length > 0) {
      selectedFile = e.target.files[0];
      dropZone.text("File selezionato: " + selectedFile.name);
    }
  });

  // Clic su "Anonimizza"
  $("#anonimizzaBtn").click(async function() {
    if (!selectedFile) {
      alert("Seleziona o trascina un file prima di cliccare Anonimizza.");
      return;
    }

    // Creiamo il FormData con il file
    let formData = new FormData();
    formData.append("file", selectedFile);

    // Inviamo l'AJAX al backend
    try {
      const response = await $.ajax({
        url: "http://localhost:5000/api/anonymize",  // Adatta se la porta è diversa
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
        dataType: "json" // Riceviamo JSON
      });

      if (response.error) {
        alert("Errore dal server: " + response.error);
        return;
      }

      // response = { anonymized_text, zip_base64 }
      // Mostriamo il testo anonimizzato
      $("#anonText").text(response.anonymized_text);

      // Scarichiamo subito lo zip
      if (response.zip_base64) {
        downloadZip(response.zip_base64);
      }

    } catch (err) {
      console.error("Errore AJAX: ", err);
      alert("Si è verificato un errore durante l'anonimizzazione.");
    }
  });
});

function downloadZip(base64Data) {
  const link = document.createElement("a");
  link.href = "data:application/zip;base64," + base64Data;
  link.download = "anonymized_package.zip";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Esempio: parte di "De-anonimizzazione"
$(document).ready(function () {
    const dropZone = $("#dropZone");
    const fileInput = $("#fileInput");
  
    // Gestione del DRAG & DROP (identico a index.html, 
    // se vuoi mantenere la stessa logica)
    dropZone.on("dragenter", function(e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.addClass("hover");
    });
  
    dropZone.on("dragleave", function(e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.removeClass("hover");
    });
  
    dropZone.on("dragover", function(e) {
      e.preventDefault();
      e.stopPropagation();
    });
  
    dropZone.on("drop", function(e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.removeClass("hover");
  
      const files = e.originalEvent.dataTransfer.files;
      if (files && files.length > 0) {
        selectedFile = files[0];
        dropZone.text("File selezionato: " + selectedFile.name);
      }
    });
  
    // Apertura del selettore file
    $("#selectFileBtn").click(function() {
      fileInput.click();
    });
  
    fileInput.change(function(e) {
      if (e.target.files && e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        dropZone.text("File selezionato: " + selectedFile.name);
      }
    });
  
    // Clic su "De-anonimizza"
    $("#deanonimizzaBtn").click(async function() {
      if (!selectedFile) {
        alert("Seleziona o trascina un file prima di cliccare De-anonimizza.");
        return;
      }
  
      let formData = new FormData();
      formData.append("file", selectedFile);
  
      try {
        const response = await $.ajax({
          url: "http://localhost:5000/api/deanonymize",  // Endpoint di DE-anonimizzazione
          method: "POST",
          data: formData,
          contentType: false,
          processData: false,
          dataType: "json"
        });
  
        if (response.error) {
          alert("Errore dal server: " + response.error);
          return;
        }
  
        // Esempio di oggetto di risposta
        // { deanon_text: "...", ... }
        $("#deanonText").text(response.deanon_text);
  
        // Se il server restituisce un file da scaricare in Base64
        if (response.zip_base64) {
          downloadZip(response.zip_base64);
        }
  
      } catch (err) {
        console.error("Errore AJAX: ", err);
        alert("Si è verificato un errore durante la de-anonimizzazione.");
      }
    });
  });
  