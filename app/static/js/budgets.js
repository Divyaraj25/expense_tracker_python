// Global variables
let currentEditingBudgetId = null;
let budgets = [];
let categories = [];

// DOM Elements
const budgetsList = document.getElementById("budgetsList");
const loadingState = document.getElementById("loadingState");
const budgetForm = document.getElementById("budgetForm");
const filterCategory = document.getElementById("filterCategory");
const filterPeriod = document.getElementById("filterPeriod");

// Format currency
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Format date for display with timezone handling
function formatDate(dateString) {
  console.log(dateString);
  if (!dateString) return "N/A";
  const options = {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "Asia/Kolkata",
  };

  // Handle both string and Date objects
  const date =
    typeof dateString === "string" ? new Date(dateString) : dateString;

  // Ensure we have a valid date
  if (isNaN(date.getTime())) return "Invalid Date";

  // Format with Indian timezone
  return date.toLocaleDateString("en-IN", options);
}

// Format date for input fields
function formatDateForInput(date) {
  return date.toISOString().split("T")[0];
}

// Show alert message
function showAlert(type, message) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.role = "alert";
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  const alertContainer =
    document.querySelector(".alert-container") || document.body;
  alertContainer.prepend(alertDiv);

  // Auto-remove alert after 5 seconds
  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}

// Load categories from the server
async function loadCategories() {
  try {
    if (!localStorage.getItem("isAuthenticated")) {
      console.error("User not authenticated");
      return [];
    }

    showLoading(true);
    const response = await fetch("/api/transactions/categories", {
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(
        `Failed to load categories: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();

    // Reset categories array
    categories = [];

    // Handle the specific category structure: { expense: [...], income: [...], transfer: [...] }
    if (
      data &&
      typeof data === "object" &&
      data.expense &&
      Array.isArray(data.expense)
    ) {
      // For budgets, we only need expense categories
      categories = data.expense.map((category) => ({
        name: category,
        type: "expense",
      }));

      // Store all categories in localStorage for other uses if needed
      localStorage.setItem("allCategories", JSON.stringify(data));
    } else {
      console.warn("No expense categories found in response:", data);
      // Set default categories if none found
      categories = [
        { name: "food", type: "expense" },
        { name: "transportation", type: "expense" },
        { name: "housing", type: "expense" },
        { name: "entertainment", type: "expense" },
        { name: "shopping", type: "expense" },
        { name: "health", type: "expense" },
        { name: "education", type: "expense" },
        { name: "bills", type: "expense" },
        { name: "other", type: "expense" },
      ];
      localStorage.setItem(
        "allCategories",
        JSON.stringify({ expense: categories.map((c) => c.name) })
      );
    }

    console.log("Loaded categories:", categories);

    // Populate category dropdowns
    populateCategoryDropdown("budgetCategory", "Select a category");
    populateCategoryDropdown("filterCategory", "All Categories");

    return categories;
  } catch (error) {
    console.error("Error loading categories:", error);
    showAlert(
      "warning",
      "Using default categories. Some features may be limited."
    );
    return [];
  } finally {
    showLoading(false);
  }
}

// Populate category dropdown
function populateCategoryDropdown(elementId, defaultText) {
  const dropdown = document.getElementById(elementId);
  if (!dropdown) return;

  // Save current value
  const currentValue = dropdown.value;

  // Clear and add default option
  dropdown.innerHTML = `<option value="">${defaultText}</option>`;

  // Add categories
  categories.forEach((category) => {
    const option = document.createElement("option");
    // Handle different category object structures
    const categoryValue =
      category.name || category.value || category.id || category;
    const categoryText =
      category.display_name || category.name || category.value || category;

    option.value = categoryValue;
    option.textContent = categoryText;
    dropdown.appendChild(option);
  });

  // Restore value if it still exists
  if (
    currentValue &&
    Array.from(dropdown.options).some((opt) => opt.value === currentValue)
  ) {
    dropdown.value = currentValue;
  }
}

// Load budgets from the server
async function loadBudgets() {
  try {
    if (!localStorage.getItem("isAuthenticated")) {
      console.error("User not authenticated");
      return [];
    }

    showLoading(true);
    const response = await fetch("/api/budgets", {
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // Important for session cookies
    });

    if (!response.ok) {
      throw new Error("Failed to load budgets");
    }

    const data = await response.json();
    budgets = Array.isArray(data) ? data : data.budgets || [];

    renderBudgets(budgets);
    updateStats();
    return budgets;
  } catch (error) {
    console.error("Error loading budgets:", error);
    showAlert("danger", "Failed to load budgets");
    return [];
  } finally {
    showLoading(false);
  }
}

// Render budgets to the page
function renderBudgets(budgetsToRender) {
  if (!budgetsList) return;

  if (!budgetsToRender || budgetsToRender.length === 0) {
    budgetsList.innerHTML = `
      <div class="col-12">
        <div class="text-center py-5">
          <i class="fas fa-wallet fa-3x text-muted mb-3"></i>
          <h5>No budgets found</h5>
          <p class="text-muted">Create your first budget to get started</p>
          <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#budgetModal" onclick="resetForm()">
            <i class="fas fa-plus me-2"></i>Add Budget
          </button>
        </div>
      </div>
    `;
    return;
  }

  budgetsList.innerHTML = budgetsToRender
    .map((budget) => {
      const spent = budget.spent || 0;
      const remaining = budget.amount - spent;
      const progress = Math.min(100, (spent / budget.amount) * 100);

      return `
      <div class="col-md-6 col-lg-4 mb-4" data-budget-id="${budget.id}">
        <div class="card h-100 budget-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="card-title mb-0">
                <i class="fas fa-${getCategoryIcon(
                  budget.category
                )} text-primary me-2"></i>
                ${budget.category}
              </h5>
              <span class="badge bg-${getPeriodBadgeColor(budget.period)}">
                ${capitalizeFirstLetter(budget.period)}
              </span>
            </div>
            
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div>
                <small class="text-muted">Spent</small>
                <h4 class="mb-0">${formatCurrency(spent)}</h4>
              </div>
              <div class="text-end">
                <small class="text-muted">Remaining</small>
                <h4 class="mb-0 ${
                  remaining < 0 ? "text-danger" : "text-success"
                }">
                  ${formatCurrency(remaining)}
                </h4>
              </div>
            </div>
            
            <div class="progress mb-3" style="height: 8px;">
              <div class="progress-bar bg-${
                progress > 90 ? "danger" : progress > 70 ? "warning" : "success"
              }" 
                   role="progressbar" 
                   style="width: ${progress}%" 
                   aria-valuenow="${progress}" 
                   aria-valuemin="0" 
                   aria-valuemax="100">
              </div>
            </div>
            
            <div class="d-flex justify-content-between text-muted small mb-3">
              <span>${progress.toFixed(1)}% of budget used</span>
              <span>${formatCurrency(budget.amount)} total</span>
            </div>
            
            <div class="budget-meta small text-muted">
              <div class="d-flex justify-content-between">
                <span>Start Date:</span>
                <span>${formatDate(budget.start_date)}</span>
              </div>
              ${
                budget.end_date
                  ? `
                <div class="d-flex justify-content-between">
                  <span>End Date:</span>
                  <span>${formatDate(budget.end_date)}</span>
                </div>
              `
                  : ""
              }
            </div>
            
            <div class="budget-actions">
              <button class="btn btn-sm btn-outline-primary" onclick="editBudget('${
                budget.id
              }')">
                <i class="fas fa-edit me-1"></i> Edit
              </button>
              <button class="btn btn-sm btn-outline-danger" 
                      onclick="confirmDelete('${
                        budget.id
                      }', '${budget.category.replace(/'/g, "\\'")}')">
                <i class="fas fa-trash-alt me-1"></i> Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    })
    .join("");
}

// Update statistics
function updateStats() {
  const totalBudget = budgets.reduce((sum, budget) => sum + budget.amount, 0);
  const totalSpent = budgets.reduce(
    (sum, budget) => sum + (budget.spent || 0),
    0
  );
  const remaining = totalBudget - totalSpent;

  const totalBudgetEl = document.getElementById("totalBudget");
  const totalSpentEl = document.getElementById("totalSpent");
  const remainingBudgetEl = document.getElementById("remainingBudget");

  if (totalBudgetEl) totalBudgetEl.textContent = formatCurrency(totalBudget);
  if (totalSpentEl) totalSpentEl.textContent = formatCurrency(totalSpent);
  if (remainingBudgetEl) {
    remainingBudgetEl.textContent = formatCurrency(remaining);
    remainingBudgetEl.className = `stat-value ${
      remaining < 0 ? "text-danger" : "text-success"
    }`;
  }
}

// Show/hide loading state
function showLoading(show) {
  if (loadingState) {
    loadingState.style.display = show ? "block" : "none";
  }
  if (budgetsList && !show && budgets.length > 0) {
    budgetsList.style.display = "flex";
  } else if (budgetsList) {
    budgetsList.style.display = "block";
  }
}

// Reset form
function resetForm() {
  currentEditingBudgetId = null;
  document.getElementById("budgetForm").reset();
  document.getElementById("modalBudgetTitle").innerHTML =
    '<i class="fas fa-wallet me-2"></i>Add New Budget';
  document.getElementById("saveBudgetBtn").innerHTML =
    '<i class="fas fa-save me-1"></i> Save Budget';
  document.getElementById("budgetCategory").disabled = false;

  // Reset date to today
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("budgetStartDate").value = today;
  document.getElementById("budgetEndDate").value = "";
  document.getElementById("budgetNote").value = "";

  // Hide end date container by default
  document.getElementById("endDateContainer").style.display = "none";

  // Load a new tip when the form is reset
  loadNewTip();
}

// Handle form submission
async function handleBudgetSubmit(e) {
  e.preventDefault();

  const form = e.target;
  if (!form.checkValidity()) {
    e.stopPropagation();
    form.classList.add("was-validated");
    return;
  }

  const budgetData = {
    category: document.getElementById("budgetCategory").value,
    amount: parseFloat(document.getElementById("budgetAmount").value),
    period: document.getElementById("budgetPeriod").value,
    start_date: document.getElementById("budgetStartDate").value,
    end_date: document.getElementById("budgetEndDate").value || null,
    note: document.getElementById("budgetNote").value.trim(),
  };

  const saveButton = document.getElementById("saveBudgetBtn");
  const originalButtonText = saveButton.innerHTML;

  try {
    saveButton.disabled = true;
    saveButton.innerHTML = `
      <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
      ${currentEditingBudgetId ? "Updating..." : "Saving..."}
    `;

    const url = currentEditingBudgetId
      ? `/api/budgets/${currentEditingBudgetId}`
      : "/api/budgets";

    const method = currentEditingBudgetId ? "PUT" : "POST";

    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // Important for session cookies
      body: JSON.stringify(budgetData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || "Failed to save budget");
    }

    // Close modal and reload budgets
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("budgetModal")
    );
    if (modal) modal.hide();

    showAlert(
      "success",
      `Budget ${currentEditingBudgetId ? "updated" : "created"} successfully`
    );
    loadBudgets();
  } catch (error) {
    console.error("Error saving budget:", error);
    showAlert("danger", error.message || "Failed to save budget");
  } finally {
    saveButton.disabled = false;
    saveButton.innerHTML = originalButtonText;
  }
}

// Edit budget
async function editBudget(id) {
  try {
    const budget = budgets.find((b) => b.id === id);
    if (!budget) throw new Error("Budget not found");

    currentEditingBudgetId = id;

    // Set form values
    document.getElementById("budgetCategory").value = budget.category;
    document.getElementById("budgetAmount").value = budget.amount;
    document.getElementById("budgetPeriod").value = budget.period;
    document.getElementById("budgetStartDate").value = budget.start_date;
    document.getElementById("budgetEndDate").value = budget.end_date || "";
    document.getElementById("budgetNote").value = budget.note || "";

    if (budget.end_date) {
      document.getElementById("endDateContainer").style.display = "block";
    }

    // Update modal title
    document.getElementById("modalBudgetTitle").innerHTML = `
      <i class="fas fa-edit me-2"></i>Edit Budget
    `;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById("budgetModal"));
    modal.show();
  } catch (error) {
    console.error("Error editing budget:", error);
    showAlert("danger", error.message || "Failed to edit budget");
  }
}

// Confirm delete
function confirmDelete(id, category) {
  currentEditingBudgetId = id;
  document.getElementById("deleteCategoryName").textContent = category;
  const modal = new bootstrap.Modal(document.getElementById("deleteModal"));
  modal.show();
}

// Delete budget
async function deleteBudget() {
  try {
    const response = await fetch(`/api/budgets/${currentEditingBudgetId}`, {
      method: "DELETE",
      credentials: "include", // Important for session cookies
    });

    if (!response.ok) {
      throw new Error("Failed to delete budget");
    }

    // Close modal and reload budgets
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("deleteModal")
    );
    if (modal) modal.hide();

    showAlert("success", "Budget deleted successfully");
    loadBudgets();
  } catch (error) {
    console.error("Error deleting budget:", error);
    showAlert("danger", error.message || "Failed to delete budget");
  }
}

// Reset filters
function resetFilters() {
  if (filterCategory) filterCategory.value = "";
  if (filterPeriod) filterPeriod.value = "monthly";
  loadBudgets();
}

// Handle period change with timezone handling
document.getElementById("budgetPeriod").addEventListener("change", function () {
  const endDateContainer = document.getElementById("endDateContainer");
  if (this.value === "custom") {
    endDateContainer.style.display = "block";
  } else {
    endDateContainer.style.display = "none";

    // Update end date based on period
    const startDateInput = document.getElementById("budgetStartDate");
    const endDateInput = document.getElementById("budgetEndDate");

    if (startDateInput.value) {
      const startDate = new Date(startDateInput.value);

      if (!isNaN(startDate.getTime())) {
        const endDate = new Date(startDate);

        switch (this.value) {
          case "daily":
            endDate.setDate(startDate.getDate() + 1);
            break;
          case "weekly":
            endDate.setDate(startDate.getDate() + 7);
            break;
          case "monthly":
            // Handle month boundaries
            const nextMonth = startDate.getMonth() + 1;
            endDate.setMonth(nextMonth);

            // If we've gone to the next year, increment year
            if (nextMonth === 0) {
              endDate.setFullYear(startDate.getFullYear() + 1);
            }

            // Handle months with different number of days
            const daysInMonth = new Date(
              endDate.getFullYear(),
              endDate.getMonth() + 1,
              0
            ).getDate();
            endDate.setDate(Math.min(startDate.getDate(), daysInMonth));
            break;
          case "yearly":
            endDate.setFullYear(startDate.getFullYear() + 1);
            // Handle leap years for February 29
            if (startDate.getMonth() === 1 && startDate.getDate() === 29) {
              const isLeapYear =
                endDate.getFullYear() % 4 === 0 &&
                (endDate.getFullYear() % 100 !== 0 ||
                  endDate.getFullYear() % 400 === 0);
              endDate.setDate(isLeapYear ? 29 : 28);
            }
            break;
        }

        // Set the end date in the input field
        endDateInput.value = formatDateForInput(endDate);
      }
    } else {
      // If no start date is selected, clear the end date
      endDateInput.value = "";
    }
  }
});

// Initialize event listeners when DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  // Get all DOM elements once
  const startDateInput = document.getElementById("budgetStartDate");
  const periodSelect = document.getElementById("budgetPeriod");
  const filterCategory = document.getElementById("filterCategory");
  const filterPeriod = document.getElementById("filterPeriod");
  const budgetForm = document.getElementById("budgetForm");
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  const endDateContainer = document.getElementById("endDateContainer");

  // Initialize end date container visibility
  if (endDateContainer) {
    endDateContainer.style.display =
      periodSelect && periodSelect.value === "custom" ? "block" : "none";
  }

  // Update end date when start date changes
  if (startDateInput) {
    startDateInput.addEventListener("change", function () {
      if (
        periodSelect &&
        periodSelect.value &&
        periodSelect.value !== "custom"
      ) {
        periodSelect.dispatchEvent(new Event("change"));
      }
    });
  }

  // Handle period change
  if (periodSelect) {
    periodSelect.addEventListener("change", function () {
      if (endDateContainer) {
        endDateContainer.style.display =
          this.value === "custom" ? "block" : "none";
      }
    });
  }

  // Handle filter changes
  if (filterCategory) filterCategory.addEventListener("change", loadBudgets);
  if (filterPeriod) filterPeriod.addEventListener("change", loadBudgets);

  // Handle form submission
  if (budgetForm) budgetForm.addEventListener("submit", handleBudgetSubmit);

  // Handle delete confirmation
  if (confirmDeleteBtn)
    confirmDeleteBtn.addEventListener("click", deleteBudget);

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.forEach(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
  );
});

// Load a new budget tip
function loadNewTip() {
  fetch("/api/budgets/tips")
    .then((response) => response.json())
    .then((data) => {
      const tipElement = document.getElementById("budgetTipText");
      if (tipElement) {
        tipElement.textContent =
          data.tip ||
          "Set realistic budgets based on your past spending patterns";
      }
    })
    .catch((error) => {
      console.error("Error loading tip:", error);
      const tipElement = document.getElementById("budgetTipText");
      if (tipElement) {
        tipElement.textContent =
          "Set realistic budgets based on your past spending patterns";
      }
    });
}

// Initialize the page
document.addEventListener("DOMContentLoaded", async function () {
  try {
    // First load categories
    await loadCategories();
    // Then load budgets
    await loadBudgets();
    // Load initial tip
    loadNewTip();
  } catch (error) {
    console.error("Initialization error:", error);
    showAlert(
      "danger",
      "Failed to initialize the application. Please refresh the page."
    );
  }
});

// Helper functions
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function getPeriodBadgeColor(period) {
  const colors = {
    daily: "info",
    weekly: "primary",
    monthly: "success",
    yearly: "warning",
    custom: "secondary",
  };
  return colors[period] || "secondary";
}

function getCategoryIcon(category) {
  const icons = {
    food: "utensils",
    transportation: "car",
    housing: "home",
    entertainment: "film",
    shopping: "shopping-bag",
    health: "heartbeat",
    education: "graduation-cap",
    bills: "file-invoice-dollar",
    other: "ellipsis-h",
  };

  const categoryLower = category.toLowerCase();
  return (
    Object.entries(icons).find(([key]) => categoryLower.includes(key))?.[1] ||
    "wallet"
  );
}

// All initialization is now handled in the main DOMContentLoaded event listener
