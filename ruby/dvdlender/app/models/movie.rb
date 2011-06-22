class Movie < ActiveRecord::Base
  validates_presence_of :title
  validates_uniqueness_of :title
  cattr_reader :per_page
  @@per_page = 10
  
  def validate
    if borrowed_on.blank? && borrower.blank? && due_on.blank?
      # ok
    elsif !borrowed_on.blank? && !borrower.blank? && !due_on.blank?
      if due_on <borrowed_on
        errors.add(:due_on, "is before date-borrowed")
      end
    elsif borrowed_on.blank?
      errors.add(:borrowed_on ,"is not specified")
    elsif borrower.blank?
      errors.add(:borrower ,"is not specified")
    else
      errors.add(:due_on ,"is not specified")
    end
  end
end
