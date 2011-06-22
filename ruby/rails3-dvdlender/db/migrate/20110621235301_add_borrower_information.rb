class AddBorrowerInformation < ActiveRecord::Migration
    def self.up
      add_column :movies, :borrower, :string, :limit => 60
      add_column :movies, :borrowed_on, :date
      add_column :movies, :due_on, :date
    end

    def self.down
      remove_column :movies, :borrower
      remove_column :movies, :borrowed_on
      remove_column :movies, :due_on
    end
end
