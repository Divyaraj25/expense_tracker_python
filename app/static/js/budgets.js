document.addEventListener("DOMContentLoaded", function () {
  loadBudgets();
  loadCategories();

  // Event listeners
  document.getElementById("saveBudget").addEventListener("click", addBudget);

  // Set today's date as default for start date
  document.getElementById("budgetStartDate").valueAsDate = new Date();
});

function loadBudgets() {
  fetch("/api/budgets/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const budgetsList = document.getElementById("budgetsList");
      budgetsList.innerHTML = "";

      data.forEach((budget) => {
        const progress = budget.progress;
        const progressPercentage = Math.min(progress.percentage, 100);
        const progressColor =
          progressPercentage < 75
            ? "success"
            : progressPercentage < 90
            ? "warning"
            : "danger";

        const col = document.createElement("div");
        col.className = "col-md-6 col-lg-4 mb-4";

        col.innerHTML = `
              <div class="card h-100">
                  <div class="card-body">
                      <div class="d-flex justify-content-between align-items-center mb-3">
                          <h6 class="card-title mb-0">${budget.category}</h6>
                          <span class="badge bg-secondary">${
                            budget.period
                          }</span>
                      </div>
                      
                      <div class="mb-3">
                          <div class="d-flex justify-content-between">
                              <span>Spent: $${parseFloat(
                                progress.spent
                              ).toFixed(2)}</span>
                              <span>Budget: $${parseFloat(
                                budget.amount
                              ).toFixed(2)}</span>
                          </div>
                          <div class="progress mt-2">
                              <div class="progress-bar bg-${progressColor}" 
                                   role="progressbar" 
                                   style="width: ${progressPercentage}%"
                                   aria-valuenow="${progressPercentage}" 
                                   aria-valuemin="0" 
                                   aria-valuemax="100">
                                  ${progressPercentage.toFixed(1)}%
                              </div>
                          </div>
                          <div class="text-center mt-2">
                              <small class="text-muted">$${parseFloat(
                                progress.remaining
                              ).toFixed(2)} remaining</small>
                          </div>
                      </div>
                      
                      <div class="small text-muted">
                          <div>Start: ${new Date(
                            budget.start_date
                          ).toLocaleDateString()}</div>
                          ${
                            budget.end_date
                              ? `<div>End: ${new Date(
                                  budget.end_date
                                ).toLocaleDateString()}</div>`
                              : ""
                          }
                      </div>
                  </div>
                  <div class="card-footer bg-transparent">
                      <button class="btn btn-sm btn-outline-primary me-1" onclick="editBudget('${
                        budget.id
                      }')">
                          <i class="fas fa-edit"></i> Edit
                      </button>
                      <button class="btn btn-sm btn-outline-danger" onclick="deleteBudget('${
                        budget.id
                      }')">
                          <i class="fas fa-trash"></i> Delete
                      </button>
                  </div>
              </div>
          `;

        budgetsList.appendChild(col);
      });
    })
    .catch((error) => {
      console.error("Error loading budgets:", error);
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
      const categorySelect = document.getElementById("budgetCategory");
      categorySelect.innerHTML = '<option value="">Select Category</option>';

      // Add expense categories (budgets are typically for expenses)
      data.expense.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error loading categories:", error);
    });
}

function addBudget() {
  const category = document.getElementById("budgetCategory").value;
  const amount = document.getElementById("budgetAmount").value;
  const period = document.getElementById("budgetPeriod").value;
  const startDate = document.getElementById("budgetStartDate").value;
  const endDate = document.getElementById("budgetEndDate").value;

  const budgetData = {
    category,
    amount,
    period,
    start_date: startDate,
  };

  if (endDate) {
    budgetData.end_date = endDate;
  }

  fetch("/api/budgets/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(budgetData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "Budget created") {
        // Close modal and reset form
        bootstrap.Modal.getInstance(
          document.getElementById("addBudgetModal")
        ).hide();
        document.getElementById("addBudgetForm").reset();

        // Reload budgets
        loadBudgets();

        // Show success message
        alert("Budget created successfully!");
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error adding budget:", error);
      alert("Error adding budget. Please try again.");
    });
}

function editBudget(id) {
  // Implementation for editing a budget
  alert("Edit budget " + id);
}

function deleteBudget(id) {
  if (confirm("Are you sure you want to delete this budget?")) {
    fetch(`/api/budgets/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message === "Budget deleted") {
          // Reload budgets
          loadBudgets();
          alert("Budget deleted successfully!");
        } else {
          alert("Error: " + data.message);
        }
      })
      .catch((error) => {
        console.error("Error deleting budget:", error);
        alert("Error deleting budget. Please try again.");
      });
  }
}
