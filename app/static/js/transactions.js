document.addEventListener("DOMContentLoaded", function () {
  loadTransactions();
  loadCategories();
  loadAccounts();

  // Event listeners
  document
    .getElementById("transactionType")
    .addEventListener("change", toggleAccountFields);
  document
    .getElementById("saveTransaction")
    .addEventListener("click", addTransaction);
});

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

        const dateCell = document.createElement("td");
        dateCell.textContent = new Date(transaction.date).toLocaleDateString();

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

function addTransaction() {
  const type = document.getElementById("transactionType").value;
  const amount = document.getElementById("transactionAmount").value;
  const category = document.getElementById("transactionCategory").value;
  const description = document.getElementById("transactionDescription").value;
  const accountFrom = document.getElementById("transactionAccountFrom").value;
  const accountTo = document.getElementById("transactionAccountTo").value;
  const date = document.getElementById("transactionDate").value;

  const transactionData = {
    type,
    amount,
    category,
    description,
    date,
  };

  if (type === "expense" || type === "transfer") {
    transactionData.account_from = accountFrom;
  }

  if (type === "income" || type === "transfer") {
    transactionData.account_to = accountTo;
  }

  fetch("/api/transactions/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(transactionData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "Transaction created") {
        // Close modal and reset form
        bootstrap.Modal.getInstance(
          document.getElementById("addTransactionModal")
        ).hide();
        document.getElementById("addTransactionForm").reset();

        // Reload transactions
        loadTransactions();

        // Show success message
        alert("Transaction added successfully!");
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error adding transaction:", error);
      alert("Error adding transaction. Please try again.");
    });
}

function editTransaction(id) {
  // Implementation for editing a transaction
  alert("Edit transaction " + id);
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
          alert("Transaction deleted successfully!");
        } else {
          alert("Error: " + data.message);
        }
      })
      .catch((error) => {
        console.error("Error deleting transaction:", error);
        alert("Error deleting transaction. Please try again.");
      });
  }
}
