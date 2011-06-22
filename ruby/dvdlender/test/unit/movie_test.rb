require 'test_helper'

class MovieTest < ActiveSupport::TestCase
  def test_present
    m = Movie.new
    assert !m.valid?
    m.title = "Rocky"
    assert m.valid?
  end
    
  def test_unique
    m1 = Movie.create(:title => "Alien")
    assert m1.valid?
    m2 = Movie.create(:title => "Alien")
    # First film should still be valid
    assert m1.valid?
    assert !m2.valid?
    m2.title += "s"
    assert m2.valid?
  end
  def test_borrower
    m = Movie.create(:title => "House")
    m.borrowed_on = Date.today
    assert !m.valid?
    m.borrower = "Dave"
    assert !m.valid?
    m.due_on = Date.yesterday # Date.today - 1 if using Rails 3.0
    assert !m.valid?
    m.due_on = m.borrowed_on + 3
    assert m.valid?

    # Now clear the borrower
    m.borrower = ""
    assert !m.valid?
  end
end
