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
  if (!localStorage.getItem('isAuthenticated')) {
    console.error('User not authenticated');
    return;
  }

  fetch("/api/transactions/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
    },
    credentials: 'include'  // Important for session cookies
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
              ${
                weekDisplay
                  ? `<small class="text-muted">${weekDisplay}</small>`
                  : ""
              }
            </div>
          `;
        } else {
          dateCell.textContent = "N/A";
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
  if (!localStorage.getItem('isAuthenticated')) {
    console.error('User not authenticated');
    return;
  }

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
  if (!localStorage.getItem('isAuthenticated')) {
    console.error('User not authenticated');
    return;
  }

  fetch("/api/accounts", {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
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
  // Get form elements
  const type = document.getElementById("transactionType").value;
  const amount = document.getElementById("transactionAmount").value;
  const category = document.getElementById("transactionCategory").value;
  const description = document.getElementById("transactionDescription").value;
  const accountFrom = document.getElementById("transactionAccountFrom")?.value || '';
  const accountTo = document.getElementById("transactionAccountTo")?.value || '';
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

  // Validate required fields
  const requiredFields = {
    type: "Transaction type",
    amount: "Amount",
    category: "Category",
    date: "Date",
    time: "Time",
  };

  // Debug: Log all form values
  console.log("Form values:", {
    type,
    amount,
    category,
    description,
    accountFrom,
    accountTo,
    date,
    time,
  });

  // Check for missing required fields
  const missingFields = [];

  if (!type || type.trim() === "") {
    missingFields.push(requiredFields.type);
  }
  if (!amount || amount.trim() === "") {
    missingFields.push(requiredFields.amount);
  }
  if (!category || category.trim() === "") {
    missingFields.push(requiredFields.category);
  }
  if (!date || date.trim() === "") {
    missingFields.push(requiredFields.date);
  }
  if (!time || time.trim() === "") {
    missingFields.push(requiredFields.time);
  }

  // Additional validation based on transaction type
  if ((type === "expense" || type === "transfer") && !accountFrom) {
    missingFields.push("Source Account");
  }
  if ((type === "income" || type === "transfer") && !accountTo) {
    missingFields.push("Destination Account");
  }

  if (missingFields.length > 0) {
    throw new Error(`Missing required fields: ${missingFields.join(", ")}`);
  }

  // Prepare request data
  const requestData = {
    type,
    amount: parseFloat(amount),
    category,
    description: description || "",
    date: date,
    time: time,
  };

  // Add account fields based on transaction type
  if (type === "expense" || type === "transfer") {
    requestData.account_from = accountFrom;
  }
  if (type === "income" || type === "transfer") {
    requestData.account_to = accountTo;
  }

  fetch(url, {
    method: method,
    headers: {
      "Content-Type": "application/json"
    },
    credentials: 'include',  // Important for session cookies
    body: JSON.stringify(requestData),
  })
    .then(async (response) => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        console.error('Server response error:', response.status, data);
        throw new Error(data.message || `Server responded with status ${response.status}`);
      }
      return data;
    })
    .then((data) => {
      // Close the modal
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("addTransactionModal")
      );
      if (modal) {
        modal.hide();
      }

      // Reset the form
      const form = document.getElementById("addTransactionForm");
      if (form) {
        form.reset();
      }

      // Reload transactions and refresh budgets
      loadTransactions();
      refreshBudgets();

      // Show success message
      showAlert(
        `Transaction ${
          window.currentEditId ? "updated" : "added"
        } successfully!`,
        "success"
      );

      // Reset edit ID
      window.currentEditId = null;
    })
    .catch((error) => {
      console.error(
        `Error ${window.currentEditId ? "updating" : "adding"} transaction:`,
        error
      );

      let errorMessage = error.message || "An unknown error occurred";

      // Handle common error cases
      if (error.message.includes("400")) {
        errorMessage = "Invalid data. Please check your input and try again.";
      } else if (error.message.includes("401") || error.message.includes("403")) {
        errorMessage = "You need to be logged in to perform this action.";
      } else if (error.message.includes("404")) {
        errorMessage = "The requested resource was not found.";
      } else if (error.message.includes("500") || error.message.includes("Server Error")) {
        errorMessage = "A server error occurred. Please try again later.";
        errorMessage = "Server error. Please try again later.";
      }

      showAlert(
        `Error ${
          window.currentEditId ? "updating" : "adding"
        } transaction: ${errorMessage}`,
        "danger"
      );
    });
}

function editTransaction(id) {
  fetch(`/api/transactions/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
    },
    credentials: 'include'  // Important for session cookies
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch transaction details");
      }
      return response.json();
    })
    .then((data) => {
      const transaction = data.data || data;

      // Set the modal title
      const modalTitle = document.querySelector(
        "#addTransactionModal .modal-title"
      );
      if (modalTitle) {
        modalTitle.textContent = "Edit Transaction";
      }

      // Set form values
      const transactionId = document.getElementById("transactionId");
      const transactionType = document.getElementById("transactionType");
      const transactionAmount = document.getElementById("transactionAmount");
      const transactionCategory = document.getElementById(
        "transactionCategory"
      );
      const transactionDescription = document.getElementById(
        "transactionDescription"
      );

      if (transactionId) transactionId.value = id;
      if (transactionType) transactionType.value = transaction.type || "";
      if (transactionAmount) transactionAmount.value = transaction.amount || "";
      if (transactionCategory) {
        transactionCategory.value =
          transaction.category_id || transaction.category || "";
      }
      if (transactionDescription) {
        transactionDescription.value = transaction.description || "";
      }

      // Set date and time using the pre-formatted strings from the backend
      const transactionDate = document.getElementById("transactionDate");
      const transactionTime = document.getElementById("transactionTime");

      if (transactionDate) {
        if (transaction.date_str) {
          transactionDate.value = transaction.date_str;
        } else if (transaction.date) {
          // If we have a date object instead of string
          const date = new Date(transaction.date);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, "0");
          const day = String(date.getDate()).padStart(2, "0");
          transactionDate.value = `${year}-${month}-${day}`;
        }
      }

      if (transactionTime) {
        if (transaction.time_str) {
          transactionTime.value = transaction.time_str;
        } else if (transaction.time) {
          transactionTime.value = transaction.time;
        } else {
          // Fallback to current time if no time is provided
          const now = new Date();
          const hours = String(now.getHours()).padStart(2, "0");
          const minutes = String(now.getMinutes()).padStart(2, "0");
          transactionTime.value = `${hours}:${minutes}`;
        }
      }

      // Set accounts
      if (transaction.account_from) {
        document.getElementById("transactionAccountFrom").value =
          transaction.account_from;
      }
      if (transaction.account_to) {
        document.getElementById("transactionAccountTo").value =
          transaction.account_to;
      }

      // Show the accounts section based on transaction type
      toggleAccountFields();

      // Set the current edit ID
      window.currentEditId = id;

      // Show the modal
      const modal = new bootstrap.Modal(
        document.getElementById("addTransactionModal")
      );
      modal.show();
    })
    .catch((error) => {
      console.error("Error fetching transaction:", error);
      showAlert("Error loading transaction details", "danger");
    });
}

function deleteTransaction(id) {
  if (confirm("Are you sure you want to delete this transaction?")) {
    fetch(`/api/transactions/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message && data.message.includes("deleted")) {
          // Reload transactions and budgets
          loadTransactions();
          refreshBudgets();
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

// Refresh budget data
function refreshBudgets() {
  if (typeof loadBudgets === 'function') {
    loadBudgets();
  } else if (window.location.pathname.includes('budgets')) {
    // If we're on the budgets page, trigger a page reload
    window.location.reload();
  }
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
