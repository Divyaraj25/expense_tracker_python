document.addEventListener("DOMContentLoaded", function () {
  loadAccounts();

  // Event listeners
  document
    .getElementById("accountType")
    .addEventListener("change", toggleAccountFields);
  document.getElementById("saveAccount").addEventListener("click", addAccount);
});

function toggleAccountFields() {
  const type = document.getElementById("accountType").value;
  const bankNameField = document.getElementById("bankNameField");
  const lastFourField = document.getElementById("lastFourField");

  if (type === "bank" || type === "card") {
    bankNameField.style.display = "block";
    lastFourField.style.display = "block";
  } else {
    bankNameField.style.display = "none";
    lastFourField.style.display = "none";
  }
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
      const accountsList = document.getElementById("accountsList");
      accountsList.innerHTML = "";

      data.forEach((account) => {
        const col = document.createElement("div");
        col.className = "col-md-6 col-lg-4 mb-4";

        let icon = "fa-wallet";
        let bgColor = "primary";

        if (account.type === "bank") {
          icon = "fa-building";
          bgColor = "info";
        } else if (account.type === "card") {
          icon = "fa-credit-card";
          bgColor = "success";
        }

        col.innerHTML = `
              <div class="card h-100">
                  <div class="card-body">
                      <div class="d-flex justify-content-between align-items-center mb-3">
                          <div class="bg-${bgColor} p-3 rounded-circle">
                              <i class="fas ${icon} fa-2x text-white"></i>
                          </div>
                          <div class="text-end">
                              <h5 class="card-title mb-0">$${parseFloat(
                                account.balance
                              ).toFixed(2)}</h5>
                              <small class="text-muted">Balance</small>
                          </div>
                      </div>
                      <h6 class="card-subtitle mb-2">${account.name}</h6>
                      <p class="card-text text-muted small">
                          ${
                            account.type.charAt(0).toUpperCase() +
                            account.type.slice(1)
                          }
                          ${account.bank_name ? "• " + account.bank_name : ""}
                          ${
                            account.last_four
                              ? "• ****" + account.last_four
                              : ""
                          }
                      </p>
                      ${
                        account.details
                          ? `<p class="card-text">${account.details}</p>`
                          : ""
                      }
                  </div>
                  <div class="card-footer bg-transparent">
                      <button class="btn btn-sm btn-outline-primary me-1" onclick="editAccount('${
                        account.id
                      }')">
                          <i class="fas fa-edit"></i> Edit
                      </button>
                      <button class="btn btn-sm btn-outline-danger" onclick="deleteAccount('${
                        account.id
                      }')">
                          <i class="fas fa-trash"></i> Delete
                      </button>
                  </div>
              </div>
          `;

        accountsList.appendChild(col);
      });
    })
    .catch((error) => {
      console.error("Error loading accounts:", error);
    });
}

function addAccount() {
  const name = document.getElementById("accountName").value;
  const type = document.getElementById("accountType").value;
  const balance = document.getElementById("accountBalance").value;
  const bankName = document.getElementById("bankName").value;
  const lastFour = document.getElementById("lastFour").value;
  const details = document.getElementById("accountDetails").value;

  const accountData = {
    name,
    type,
    balance,
    details,
  };

  if (type === "bank" || type === "card") {
    accountData.bank_name = bankName;
    accountData.last_four = lastFour;
  }

  fetch("/api/accounts/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(accountData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "Account created") {
        // Close modal and reset form
        bootstrap.Modal.getInstance(
          document.getElementById("addAccountModal")
        ).hide();
        document.getElementById("addAccountForm").reset();

        // Reload accounts
        loadAccounts();

        // Show success message
        alert("Account added successfully!");
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error adding account:", error);
      alert("Error adding account. Please try again.");
    });
}

function editAccount(id) {
  // Implementation for editing an account
  alert("Edit account " + id);
}

function deleteAccount(id) {
  if (
    confirm(
      "Are you sure you want to delete this account? This action cannot be undone."
    )
  ) {
    fetch(`/api/accounts/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message === "Account deleted") {
          // Reload accounts
          loadAccounts();
          alert("Account deleted successfully!");
        } else {
          alert("Error: " + data.message);
        }
      })
      .catch((error) => {
        console.error("Error deleting account:", error);
        alert("Error deleting account. Please try again.");
      });
  }
}
