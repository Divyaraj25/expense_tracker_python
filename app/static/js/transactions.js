// Function to set default time
function setDefaultTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  document.getElementById("transactionTime").value = `${hours}:${minutes}`;

  // Also set default date to today
  document.getElementById("transactionDate").value = now
    .toISOString()
    .split("T")[0];
}

document.addEventListener("DOMContentLoaded", function () {
  loadTransactions();
  loadCategories();
  loadAccounts();
  setDefaultTime();

  // Event listeners
  document
    .getElementById("transactionType")
    .addEventListener("change", toggleAccountFields);
  document
    .getElementById("saveTransaction")
    .addEventListener("click", saveTransaction);
  document
    .getElementById("addTransactionModal")
    .addEventListener("hidden.bs.modal", resetForm);
});

function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

function toggleAccountFields() {
  const type = document.getElementById("transactionType").value;
  const fromField = document.getElementById("accountFromField");
  const toField = document.getElementById("accountToField");

  if (type === "expense") {
    fromField.style.display = "block";
    toField.style.display = "none";
  } else if (type === "income") {
    fromField.style.display = "none";
    toField.style.display = "block";
  } else if (type === "transfer") {
    fromField.style.display = "block";
    toField.style.display = "block";
  } else {
    fromField.style.display = "none";
    toField.style.display = "none";
  }
}

function loadTransactions() {
  fetch("/api/transactions/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const tableBody = document
        .getElementById("transactionsTable")
        .querySelector("tbody");
      tableBody.innerHTML = "";

      data.forEach((transaction) => {
        const row = document.createElement("tr");

        // Display the pre-formatted IST time from the backend
        const weekDisplay = transaction.week_number
          ? ` (Week ${transaction.week_number})`
          : "";

        const dateCell = document.createElement("td");
        if (transaction.date_full && transaction.time) {
          // Use the pre-formatted date and time strings from the backend (already in IST)
          dateCell.innerHTML = `
            <div class="d-flex flex-column">
              <span>${transaction.date_full} at ${transaction.time} IST</span>
              ${weekDisplay ? `<small class="text-muted">${weekDisplay}</small>` : ''}
            </div>
          `;
        } else {
          dateCell.textContent = 'N/A';
        }

        const typeCell = document.createElement("td");
        typeCell.innerHTML = `<span class="badge ${
          transaction.type === "income"
            ? "bg-success"
            : transaction.type === "expense"
            ? "bg-danger"
            : "bg-info"
        }">${transaction.type}</span>`;

        const descCell = document.createElement("td");
        descCell.textContent = transaction.description;

        const categoryCell = document.createElement("td");
        categoryCell.textContent = transaction.category;

        const amountCell = document.createElement("td");
        amountCell.className =
          transaction.type === "income" ? "text-success" : "text-danger";
        amountCell.textContent = `$${parseFloat(transaction.amount).toFixed(
          2
        )}`;

        const actionsCell = document.createElement("td");
        actionsCell.innerHTML = `
              <button class="btn btn-sm btn-outline-primary me-1" onclick="editTransaction('${transaction.id}')">
                  <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteTransaction('${transaction.id}')">
                  <i class="fas fa-trash"></i>
              </button>
          `;

        row.appendChild(dateCell);
        row.appendChild(typeCell);
        row.appendChild(descCell);
        row.appendChild(categoryCell);
        row.appendChild(amountCell);
        row.appendChild(actionsCell);

        tableBody.appendChild(row);
      });
    })
    .catch((error) => {
      console.error("Error loading transactions:", error);
    });
}

function loadCategories() {
  fetch("/api/transactions/categories", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const categorySelect = document.getElementById("transactionCategory");
      categorySelect.innerHTML = '<option value="">Select Category</option>';

      // Add expense categories
      data.expense.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        option.dataset.type = "expense";
        categorySelect.appendChild(option);
      });

      // Add income categories
      data.income.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        option.dataset.type = "income";
        categorySelect.appendChild(option);
      });

      // Add transfer categories
      data.transfer.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        option.dataset.type = "transfer";
        categorySelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error loading categories:", error);
    });
}

function loadAccounts() {
  fetch("/api/accounts/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const fromSelect = document.getElementById("transactionAccountFrom");
      const toSelect = document.getElementById("transactionAccountTo");

      fromSelect.innerHTML = '<option value="">Select Account</option>';
      toSelect.innerHTML = '<option value="">Select Account</option>';

      data.forEach((account) => {
        const fromOption = document.createElement("option");
        fromOption.value = account.id;
        fromOption.textContent = account.name;

        const toOption = document.createElement("option");
        toOption.value = account.id;
        toOption.textContent = account.name;

        fromSelect.appendChild(fromOption.cloneNode(true));
        toSelect.appendChild(toOption);
      });
    })
    .catch((error) => {
      console.error("Error loading accounts:", error);
    });
}

function saveTransaction() {
  const type = document.getElementById("transactionType").value;
  const amount = document.getElementById("transactionAmount").value;
  const category = document.getElementById("transactionCategory").value;
  const description = document.getElementById("transactionDescription").value;
  const accountFrom = document.getElementById("transactionAccountFrom").value;
  const accountTo = document.getElementById("transactionAccountTo").value;
  const date = document.getElementById("transactionDate").value;
  const time = document.getElementById("transactionTime").value;

  const transactionData = {
    type,
    amount,
    category,
    description,
    date,
    time,
  };

  if (type === "expense" || type === "transfer") {
    transactionData.account_from = accountFrom;
  }

  if (type === "income" || type === "transfer") {
    transactionData.account_to = accountTo;
  }

  const url = window.currentEditId
    ? `/api/transactions/${window.currentEditId}`
    : "/api/transactions/";
  const method = window.currentEditId ? "PUT" : "POST";

  fetch(url, {
    method: method,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(transactionData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (
        data.message.includes("created") ||
        data.message.includes("updated")
      ) {
        // Close modal and reset form
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("addTransactionModal")
        );
        modal.hide();
        resetForm();

        // Reload transactions
        loadTransactions();

        // Show success message
        showAlert(
          `Transaction ${
            window.currentEditId ? "updated" : "added"
          } successfully!`,
          "success"
        );
      } else {
        throw new Error(data.message || "An error occurred");
      }
    })
    .catch((error) => {
      console.error(
        `Error ${window.currentEditId ? "updating" : "adding"} transaction:`,
        error
      );
      showAlert(
        `Error ${window.currentEditId ? "updating" : "adding"} transaction: ${
          error.message
        }`,
        "danger"
      );
    });
}

function editTransaction(id) {
  fetch(`/api/transactions/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => response.json())
    .then((transaction) => {
      // Set the modal title
      document.getElementById('transactionModalLabel').textContent = 'Edit Transaction';

      // Set form values
      document.getElementById('transactionType').value = transaction.type;
      document.getElementById('transactionAmount').value = transaction.amount;
      document.getElementById('transactionCategory').value = transaction.category;
      document.getElementById('transactionDescription').value = transaction.description;

      // Set date and time using the pre-formatted strings from the backend
      if (transaction.date_str) {
        document.getElementById("transactionDate").value = transaction.date_str;
      }
      if (transaction.time_str) {
        document.getElementById("transactionTime").value = transaction.time_str;
      } else {
        // Fallback to current time if no time is provided
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        document.getElementById("transactionTime").value = `${hours}:${minutes}`;
      }

      // Set accounts
      if (transaction.account_from) {
        document.getElementById("transactionAccountFrom").value = transaction.account_from;
      }
      if (transaction.account_to) {
        document.getElementById("transactionAccountTo").value = transaction.account_to;
      }

      // Show the accounts section based on transaction type
      toggleAccountFields();

      // Set the current edit ID
      window.currentEditId = id;

      // Show the modal
      const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
      modal.show();
    })
    .catch((error) => {
      console.error('Error fetching transaction:', error);
      showAlert('Error loading transaction details', 'danger');
    });
}

function deleteTransaction(id) {
  if (confirm("Are you sure you want to delete this transaction?")) {
    fetch(`/api/transactions/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message === "Transaction deleted") {
          // Reload transactions
          loadTransactions();
          showAlert("Transaction deleted successfully!", "success");
        } else {
          throw new Error(data.message || "Failed to delete transaction");
        }
      })
      .catch((error) => {
        console.error("Error deleting transaction:", error);
        showAlert(`Error deleting transaction: ${error.message}`, "danger");
      });
  }
}

// Reset form and modal state
function resetForm() {
  const form = document.getElementById("addTransactionForm");
  if (form) form.reset();

  const modalTitle = document.querySelector(
    "#addTransactionModal .modal-title"
  );
  if (modalTitle) modalTitle.textContent = "Add Transaction";

  window.currentEditId = null;

  // Reset account fields visibility
  const fromField = document.getElementById("accountFromField");
  const toField = document.getElementById("accountToField");
  if (fromField) fromField.style.display = "none";
  if (toField) toField.style.display = "none";

  // Reset to default time and date
  setDefaultTime();
}

// Show alert message
function showAlert(message, type = "info") {
  // Remove any existing alerts
  const existingAlerts = document.querySelectorAll(".alert");
  existingAlerts.forEach((alert) => alert.remove());

  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.role = "alert";
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  const container = document.querySelector(".container:first-child");
  if (container) {
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove alert after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        alert.close();
      }
    }, 5000);
  }
}
